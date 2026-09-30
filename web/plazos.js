// Motor de cómputo de «plazos» para el navegador. Es una traducción literal de
// src/plazos/computo.py; tests/test_web.py comprueba que ambos dan lo mismo.
(function (raiz) {
  "use strict";

  const DATOS = raiz.PLAZOS_DATOS;
  const N = DATOS.normas;
  const JURISDICCIONES = ["administrativo", "civil", "contencioso", "social"];
  const UNIDADES = ["dias", "dias_naturales", "meses", "anios", "horas"];
  const JUDICIALES = ["civil", "contencioso", "social"];
  const DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"];
  const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
    "septiembre", "octubre", "noviembre", "diciembre"];

  // --- Fechas: siempre en UTC para no depender de la zona horaria del navegador ---
  const DIA_MS = 86400000;
  const fecha = (a, m, d) => new Date(Date.UTC(a, m - 1, d));
  const deIso = (s) => { const [a, m, d] = s.split("-").map(Number); return fecha(a, m, d); };
  const iso = (f) => f.toISOString().slice(0, 10);
  const mas = (f, n) => new Date(f.getTime() + n * DIA_MS);
  const anio = (f) => f.getUTCFullYear();
  const mes = (f) => f.getUTCMonth() + 1;
  const dia = (f) => f.getUTCDate();
  const semana = (f) => (f.getUTCDay() + 6) % 7; // lunes = 0, como en Python
  const dos = (n) => String(n).padStart(2, "0");
  const ddmm = (f) => `${dos(dia(f))}/${dos(mes(f))}`;
  const ddmmaaaa = (f) => `${ddmm(f)}/${anio(f)}`;

  function fechaLarga(f) {
    return `${DIAS_SEMANA[semana(f)]}, ${dia(f)} de ${MESES[mes(f) - 1]} de ${anio(f)}`;
  }

  function sumarMeses(f, n) {
    const total = mes(f) - 1 + n;
    const a = anio(f) + Math.floor(total / 12);
    const m = (total % 12) + 1;
    const ultimo = new Date(Date.UTC(a, m, 0)).getUTCDate();
    return fecha(a, m, Math.min(dia(f), ultimo));
  }

  function agostosEntre(inicio, fin) {
    let n = 0;
    for (let a = anio(inicio); a <= anio(fin); a++) {
      if (inicio < fecha(a, 8, 31) && fecha(a, 8, 1) <= fin) n++;
    }
    return n;
  }

  // --- Lugares y festivos -----------------------------------------------------
  const normalizar = (t) => t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
    .replace(/’/g, "'").split(/\s+/).filter(Boolean).join(" ");

  // Fiestas locales de los municipios (web/municipios.json, que la página carga al empezar).
  // Cada fila: [INE, nombre, comunidad, provincia, isla, días, parciales, fuente, año].
  let INDICE = null;
  function indice() {
    const M = raiz.PLAZOS_MUNICIPIOS;
    if (!M) return null;
    if (!INDICE || INDICE.origen !== M) {
      INDICE = { origen: M, porIne: new Map(), porNombre: new Map() };
      for (const f of M.municipios) {
        const m = {
          ine: f[0], nombre: f[1], ccaa: f[2], provincia: f[3], isla: f[4] || null, dias: f[5],
          parciales: f[6].map(([fecha, ambito]) => ({ fecha, ambito })), fuente: M.fuentes[f[7]], anio: f[8],
        };
        INDICE.porIne.set(`${m.anio}:${m.ine}`, m);
        const k = normalizar(m.nombre);
        if (!INDICE.porNombre.has(k)) INDICE.porNombre.set(k, []);
        INDICE.porNombre.get(k).push(m);
      }
    }
    return INDICE;
  }

  function municipioDatos(ref, a) {
    const idx = indice();
    if (!idx || !ref) return null;
    if (/^\d{5}$/.test(ref)) return idx.porIne.get(`${a}:${ref}`) || null;
    const c = (idx.porNombre.get(normalizar(ref)) || []).filter((m) => m.anio === a);
    return c.length === 1 ? c[0] : null;
  }

  function crearLugar({ ccaa = null, festivosLocales = [], isla = null, municipio = null } = {}) {
    let ine = null;
    const c = municipio ? (raiz.PLAZOS_DATOS.aniosMunicipios || []).map((a) => municipioDatos(municipio, a)).find(Boolean) : null;
    if (c) {
      if (ccaa && ccaa !== c.ccaa) throw new Error(`${c.nombre} está en ${DATOS.ccaa[c.ccaa]} (${c.ccaa}), no en ${ccaa}`);
      municipio = c.nombre;
      ine = c.ine;
      ccaa = c.ccaa;
      if (!isla) isla = c.isla;
    }
    if (ccaa && !DATOS.ccaa[ccaa]) throw new Error(`Comunidad desconocida: ${ccaa}`);
    if (isla && ccaa !== "CN") throw new Error("La isla solo se indica para Canarias");
    const unicos = [...new Set(festivosLocales.map((f) => (typeof f === "string" ? f : iso(f))))].sort();
    return { ccaa, isla, municipio, ine, festivosLocales: unicos.map(deIso) };
  }

  const datosLugar = (l, a) => (l.municipio ? municipioDatos(l.ine || l.municipio, a) : null);

  function motivosLugar(f, lugar) {
    const motivos = [];
    const clave = iso(f);
    const anual = DATOS.festivos[String(anio(f))] || {};
    if ((anual.ES || {})[clave]) motivos.push(anual.ES[clave]);
    else if (lugar.ccaa && (anual[lugar.ccaa] || {})[clave]) motivos.push(anual[lugar.ccaa][clave]);
    const insulares = DATOS.insulares[String(anio(f))];
    if (lugar.isla && insulares && insulares[lugar.isla] === clave) motivos.push(`festivo insular en ${lugar.isla}`);
    const oficiales = datosLugar(lugar, anio(f));
    const esLocal = lugar.festivosLocales.some((x) => iso(x) === clave) ||
      Boolean(oficiales && oficiales.dias.includes(clave));
    if (esLocal) motivos.push("festivo local" + (lugar.municipio ? ` en ${lugar.municipio}` : ""));
    return motivos;
  }

  function festivo(f, lugares) {
    const motivos = [];
    for (const l of lugares) for (const m of motivosLugar(f, l)) if (!motivos.includes(m)) motivos.push(m);
    return motivos.join("; ") || null;
  }

  function localesConocidos(lugares, a) {
    return lugares.every((l) => (l.festivosLocales.length && l.festivosLocales.some((x) => anio(x) === a)) ||
      datosLugar(l, a) !== null);
  }

  // --- Reglas de días inhábiles ------------------------------------------------
  function reglas(jurisdiccion, lugares, urgente) {
    const judicial = JUDICIALES.includes(jurisdiccion);
    const inhabil = (f) => {
      if (semana(f) === 5) return "sábado";
      if (semana(f) === 6) return "domingo";
      const fest = festivo(f, lugares);
      if (fest) return fest;
      if (judicial && !urgente) {
        if (mes(f) === 8) return "agosto, inhábil en los juzgados";
        if ((mes(f) === 12 && dia(f) >= 24) || (mes(f) === 1 && dia(f) <= 6)) {
          return "del 24 de diciembre al 6 de enero, inhábil en los juzgados";
        }
      }
      return null;
    };
    const siguienteHabil = (f) => {
      const saltados = [];
      let motivo;
      while ((motivo = inhabil(f))) { saltados.push({ fecha: f, motivo }); f = mas(f, 1); }
      return [f, saltados];
    };
    return { judicial, inhabil, siguienteHabil };
  }

  const normaDias = (j) => ({ administrativo: N.L39_30_2, social: N.LOPJ_185 })[j] || N.LEC_133_2;
  const normaInhabiles = (j) => ({ administrativo: N.L39_30_2, social: N.LRJS_43_4 })[j] || N.LEC_130_2;

  function resumenExcluidos(excluidos) {
    const finde = excluidos.filter((e) => e.motivo === "sábado" || e.motivo === "domingo").length;
    const partes = [];
    if (finde) partes.push(`${finde} ${finde === 1 ? "día" : "días"} de fin de semana`);
    const agrupados = new Map();
    for (const e of excluidos) {
      if (e.motivo === "sábado" || e.motivo === "domingo") continue;
      if (!agrupados.has(e.motivo)) agrupados.set(e.motivo, []);
      agrupados.get(e.motivo).push(e.fecha);
    }
    for (const [motivo, fechas] of agrupados) {
      if (fechas.length > 3) {
        partes.push(`${fechas.length} días (${ddmm(fechas[0])} a ${ddmm(fechas[fechas.length - 1])}): ${motivo}`);
      } else {
        partes.push(fechas.map(ddmmaaaa).join(", ") + `: ${motivo}`);
      }
    }
    return partes.join("; ");
  }

  // --- Cálculo ------------------------------------------------------------------
  function calcular(opciones) {
    const {
      inicio: inicioTxt, cantidad, unidad = "dias", jurisdiccion = "administrativo",
      ccaa = null, festivosLocales = [], municipio = null, isla = null, lugares: otros = [], urgente = false,
      hora = null,
    } = opciones;
    if (!JURISDICCIONES.includes(jurisdiccion)) throw new Error(`Jurisdicción desconocida: ${jurisdiccion}`);
    if (!UNIDADES.includes(unidad)) throw new Error(`Unidad desconocida: ${unidad}`);
    if (!Number.isInteger(cantidad) || cantidad < 1) throw new Error("La cantidad debe ser un número entero positivo");
    if (unidad === "dias_naturales" && jurisdiccion !== "administrativo") {
      throw new Error("Los plazos procesales se cuentan en días hábiles, no naturales");
    }
    if (urgente && jurisdiccion === "administrativo") throw new Error("'urgente' solo se aplica a plazos judiciales");
    let horaInicio = "00:00";
    if (unidad === "horas") {
      if (jurisdiccion !== "administrativo") {
        throw new Error("Los plazos por horas solo se calculan para plazos administrativos (Ley 39/2015)");
      }
      if (cantidad > 24) throw new Error("Un plazo por horas no puede pasar de 24 horas: la ley obliga a expresarlo en días");
      if (!hora || !/^\d{2}:\d{2}$/.test(hora)) {
        throw new Error("En un plazo por horas hace falta la hora de la notificación (hora='10:30')");
      }
      horaInicio = hora;
    }

    const inicio = typeof inicioTxt === "string" ? deIso(inicioTxt) : inicioTxt;
    const lista = otros.map(crearLugar);
    if (ccaa || festivosLocales.length || municipio || isla) {
      lista.unshift(crearLugar({ ccaa, festivosLocales, isla, municipio }));
    }
    const lugares = lista.length ? lista : [crearLugar()];
    const R = reglas(jurisdiccion, lugares, urgente);
    const pasos = [];
    const avisos = [];
    let excluidos = [];
    const normas = [];
    const paso = (texto, norma = null) => {
      pasos.push({ texto, norma });
      if (norma && !normas.includes(norma)) normas.push(norma);
    };

    if (jurisdiccion === "administrativo") {
      paso("Plazo administrativo: se aplica la Ley 39/2015 de Procedimiento Administrativo Común", N.L39_30_2);
    } else {
      const nombre = {
        civil: "civil (LEC)",
        contencioso: "contencioso-administrativo (LJCA; LEC supletoria)",
        social: "social (LRJS)",
      }[jurisdiccion];
      paso(`Plazo procesal del orden ${nombre}; los días inhábiles judiciales los fija la LOPJ`, N.LOPJ_182);
      if (urgente) {
        const texto = {
          social: "Modalidad procesal urgente: agosto y del 24 de diciembre al 6 de enero son hábiles",
          contencioso: "Procedimiento de derechos fundamentales: agosto es hábil",
          civil: "Actuación urgente: agosto es hábil y solo se excluyen sábados, domingos y festivos",
        };
        paso(texto[jurisdiccion], { social: N.LRJS_43_4, contencioso: N.LJCA_128_2, civil: N.LEC_133_2 }[jurisdiccion]);
        if (jurisdiccion === "contencioso") {
          avisos.push("La LJCA solo dice expresamente que agosto es hábil para los derechos " +
            "fundamentales; también se ha contado como hábil el periodo del 24 de diciembre " +
            "al 6 de enero, que da la fecha más temprana y, por tanto, la prudente.");
        }
      } else {
        paso("Agosto y los días del 24 de diciembre al 6 de enero son inhábiles", N.LOPJ_183);
      }
    }
    const lugaresTxt = lugares.map((l) => {
      const partes = l.ccaa ? [DATOS.ccaa[l.ccaa]] : [];
      if (l.isla) partes.push(`isla de ${l.isla}`);
      if (l.municipio) partes.push(l.municipio);
      if (l.festivosLocales.length) {
        const n = l.festivosLocales.length;
        partes.push(`${n} ${n === 1 ? "festivo local indicado" : "festivos locales indicados"}`);
      }
      return partes.join(", ") || "solo festivos nacionales";
    });
    if (lugaresTxt.length > 1) {
      paso("Festivos de todos los lugares indicados (" + lugaresTxt.join(" | ") +
        "): un día inhábil en cualquiera de ellos no cuenta", N.L39_30_6);
    } else {
      paso(`Calendario de festivos: ${lugaresTxt[0]}`);
    }
    if (!lugares.some((l) => l.ccaa)) {
      avisos.push("No se ha indicado comunidad autónoma: solo se descuentan los festivos nacionales.");
    }
    for (const l of lugares) {
      const d = datosLugar(l, anio(inicio));
      if (d) {
        const dias = d.dias.map((x) => ddmm(deIso(x))).join(", ") || "ninguna para todo el término";
        paso(`Fiestas locales de ${l.municipio} en ${anio(inicio)} (${dias}), según ${d.fuente.texto}`);
      }
    }

    // Avisos comunes (fiestas parciales, calendarios sin datos) y resultado.
    const cerrar = (vencimiento, pres) => {
      const limite = pres ? pres.fecha : vencimiento;
      for (const l of lugares) {
        for (const a of [...new Set([anio(inicio), anio(limite)])].sort()) {
          const d = datosLugar(l, a);
          for (const p of d ? d.parciales : []) {
            const f = deIso(p.fecha);
            if (inicio < f && f <= limite && !R.inhabil(f)) {
              avisos.push(`En ${p.ambito} (${l.municipio}) también es fiesta local el ${ddmmaaaa(f)}: ` +
                "si el plazo corre allí, ese día no cuenta y vencerá más tarde.");
            }
          }
        }
      }
      for (const a of [...new Set([anio(inicio), anio(vencimiento)])].sort()) {
        if (!localesConocidos(lugares, a)) {
          avisos.push(`Faltan los festivos locales de ${a}: si el plazo cruza alguno, vencerá más ` +
            "tarde de lo calculado aquí. Indica el municipio o sus fiestas locales.");
        }
        if (!DATOS.oficiales.includes(a)) {
          avisos.push(`El calendario de festivos de ${a} no está verificado con el BOE en esta ` +
            "versión; se usan los datos de la librería holidays.");
        }
      }

      return {
        inicio, cantidad, unidad, jurisdiccion, vencimiento, pasos, excluidos,
        advertencias: avisos, presentacionHasta: pres ? `${iso(pres.fecha)}T${pres.hora}` : null, normas,
      };
    };

    if (unidad === "horas") {
      // Ley 39/2015, art. 30.1: solo cuentan las horas de días hábiles, de hora en hora desde la notificación.
      const [hh, mm] = horaInicio.split(":").map(Number);
      let t = inicio.getTime() + (hh * 60 + mm) * 60000;
      paso("Plazo por horas: se cuenta de hora en hora y de minuto en minuto desde la notificación " +
        `(${ddmmaaaa(inicio)} a las ${horaInicio}); solo cuentan las horas de días hábiles`, N.L39_30_1);
      let restante = cantidad * 3600000;
      while (restante > 0) {
        const diaT = new Date(t - (t % DIA_MS));
        const motivo = R.inhabil(diaT);
        const siguienteDia = diaT.getTime() + DIA_MS;
        if (motivo) {
          excluidos.push({ fecha: diaT, motivo });
          t = siguienteDia;
          continue;
        }
        const hueco = siguienteDia - t;
        if (hueco >= restante) {
          t += restante;
          restante = 0;
        } else {
          restante -= hueco;
          t = siguienteDia;
        }
      }
      if (excluidos.length) paso(`Días que no cuentan: ${resumenExcluidos(excluidos)}`, N.L39_30_2);
      const finDia = t % DIA_MS === 0;
      const fechaT = new Date(t - (t % DIA_MS));
      const vence = finDia ? mas(fechaT, -1) : fechaT;
      const minutos = Math.round((t % DIA_MS) / 60000);
      const horaTxt = finDia ? "24:00" : `${dos(Math.floor(minutos / 60))}:${dos(minutos % 60)}`;
      paso(`Las ${cantidad} horas hábiles terminan el ${fechaLarga(vence)} a las ${horaTxt}`);
      return cerrar(vence, { fecha: fechaT, hora: finDia ? "00:00" : horaTxt });
    }

    const inicioComputo = mas(inicio, 1);
    paso(`El día inicial es el de la notificación o publicación (${ddmmaaaa(inicio)}); ` +
      `se empieza a contar el día siguiente, ${fechaLarga(inicioComputo)}`,
      jurisdiccion === "administrativo" ? N.L39_30_3 : N.LEC_133_1);
    const [primerHabil] = R.siguienteHabil(inicioComputo);
    if (unidad === "dias" && primerHabil.getTime() !== inicioComputo.getTime()) {
      paso(`Ese día es inhábil, así que el primer día que cuenta es el ${fechaLarga(primerHabil)}`);
    }

    let vencimiento;
    if (unidad === "dias") {
      let d = inicio;
      let contados = 0;
      while (contados < cantidad) {
        d = mas(d, 1);
        const motivo = R.inhabil(d);
        if (motivo) excluidos.push({ fecha: d, motivo });
        else contados++;
      }
      paso(`Se cuentan ${cantidad} días hábiles, sin sábados, domingos ni festivos`, normaDias(jurisdiccion));
      if (excluidos.length) paso(`Días que no cuentan: ${resumenExcluidos(excluidos)}`, normaInhabiles(jurisdiccion));
      paso(`El día hábil número ${cantidad} es el ${fechaLarga(d)}`);
      vencimiento = d;
    } else {
      let d;
      if (unidad === "dias_naturales") {
        d = mas(inicio, cantidad);
        paso(`Plazo en días naturales (solo cuando una ley lo dice así): ${cantidad} días seguidos, ` +
          `incluidos sábados, domingos y festivos, llevan al ${fechaLarga(d)}`, N.L39_30_2);
      } else {
        const meses = cantidad * (unidad === "anios" ? 12 : 1);
        let base = inicio;
        if (R.judicial && jurisdiccion === "contencioso" && !urgente && mes(inicio) === 8) {
          base = fecha(anio(inicio), 8, 31);
          paso("Notificación en agosto: el plazo no empieza a correr hasta el 1 de septiembre", N.LJCA_128_2);
          avisos.push("Con notificaciones en agosto hay resoluciones que computan el plazo de " +
            "otra forma; comprueba el criterio de tu tribunal y no apures el último día.");
        }
        d = sumarMeses(base, meses);
        const unidadTxt = unidad === "anios"
          ? `${cantidad} ${cantidad === 1 ? "año" : "años"}`
          : `${cantidad} ${cantidad === 1 ? "mes" : "meses"}`;
        const normaMeses = jurisdiccion === "administrativo" ? N.L39_30_4 : N.LEC_133_3;
        if (dia(d) !== dia(base)) {
          paso(`${unidadTxt} de fecha a fecha: el mes de vencimiento no tiene día ${dia(base)}, ` +
            `así que vence el último día del mes, el ${fechaLarga(d)}`, normaMeses);
        } else {
          paso(`${unidadTxt} de fecha a fecha: el plazo acaba el mismo día del mes, el ${fechaLarga(d)}`, normaMeses);
        }
        if (jurisdiccion === "contencioso" && !urgente) {
          let agostos = agostosEntre(base, d);
          let extra = 0;
          while (agostos > extra) {
            extra = agostos;
            d = sumarMeses(base, meses + extra);
            agostos = agostosEntre(base, d);
          }
          if (extra) {
            paso(`En agosto no corre el plazo: se añade${extra > 1 ? "n" : ""} ${extra} ` +
              `${extra === 1 ? "mes" : "meses"} y pasa al ${fechaLarga(d)}`, N.LJCA_128_2);
          }
        } else if (R.judicial && !urgente && agostosEntre(base, d)) {
          avisos.push("El plazo cruza agosto. Hay tribunales que no computan agosto en los plazos " +
            "procesales por meses; aquí no se descuenta, que es la fecha más temprana.");
        }
      }
      const [nuevo, saltados] = R.siguienteHabil(d);
      if (saltados.length) {
        excluidos = excluidos.concat(saltados);
        paso(`El último día es inhábil (${resumenExcluidos(saltados)}); se prorroga al siguiente ` +
          `hábil, el ${fechaLarga(nuevo)}`, jurisdiccion === "administrativo" ? N.L39_30_5 : N.LEC_133_4);
      }
      vencimiento = nuevo;
    }

    let presentacion = null;
    if (jurisdiccion === "administrativo") {
      paso("En el registro electrónico se puede presentar hasta las 23:59:59 del último día", N.L39_31_2);
    } else {
      const [siguiente] = R.siguienteHabil(mas(vencimiento, 1));
      presentacion = siguiente;
      paso(`El plazo expira a las 24:00 del ${ddmmaaaa(vencimiento)}, pero el escrito puede presentarse ` +
        `hasta las 15:00 del día hábil siguiente, el ${fechaLarga(siguiente)}`,
        jurisdiccion === "social" ? N.LRJS_45_1 : N.LEC_135_5);
    }

    return cerrar(vencimiento, presentacion ? { fecha: presentacion, hora: "15:00" } : null);
  }


  // --- Pago de deudas tributarias (LGT, art. 62) --------------------------------
  function plazoPago(opciones) {
    const {
      notificacion: notifTxt, periodo = "voluntario",
      ccaa = null, festivosLocales = [], municipio = null, isla = null,
    } = opciones;
    if (!["voluntario", "apremio"].includes(periodo)) throw new Error("El periodo debe ser 'voluntario' o 'apremio'");
    const notificacion = typeof notifTxt === "string" ? deIso(notifTxt) : notifTxt;
    const lista = [];
    if (ccaa || festivosLocales.length || municipio || isla) lista.push(crearLugar({ ccaa, festivosLocales, isla, municipio }));
    const lugares = lista.length ? lista : [crearLugar()];
    const R = reglas("administrativo", lugares, false);
    const pasos = [];
    const avisos = [];
    const normas = [];
    const paso = (texto, norma = null) => {
      pasos.push({ texto, norma });
      if (norma && !normas.includes(norma)) normas.push(norma);
    };
    const primera = dia(notificacion) <= 15;
    let norma, meses, d, que, destino;
    if (periodo === "voluntario") {
      norma = N.LGT_62_2;
      [meses, d] = primera ? [1, 20] : [2, 5];
      que = "la liquidación";
      destino = primera ? "del mes siguiente" : "del segundo mes siguiente";
    } else {
      norma = N.LGT_62_5;
      [meses, d] = primera ? [0, 20] : [1, 5];
      que = "la providencia de apremio";
      destino = primera ? "del mismo mes" : "del mes siguiente";
    }
    const base = sumarMeses(fecha(anio(notificacion), mes(notificacion), 1), meses);
    const nominal = fecha(anio(base), mes(base), d);
    const quincena = primera ? "entre el 1 y el 15" : "entre el 16 y el último día";
    paso(`Pago de una deuda tributaria en periodo ${periodo === "voluntario" ? "voluntario" : "ejecutivo"}: ` +
      `${que} se notificó el ${ddmmaaaa(notificacion)}, ${quincena} del mes, así que se puede pagar ` +
      `hasta el día ${d} ${destino}, el ${fechaLarga(nominal)}`, norma);
    const lugaresTxt = lugares.map((l) => {
      const partes = l.ccaa ? [DATOS.ccaa[l.ccaa]] : [];
      if (l.isla) partes.push(`isla de ${l.isla}`);
      if (l.municipio) partes.push(l.municipio);
      if (l.festivosLocales.length) {
        const n = l.festivosLocales.length;
        partes.push(`${n} ${n === 1 ? "festivo local indicado" : "festivos locales indicados"}`);
      }
      return partes.join(", ") || "solo festivos nacionales";
    });
    paso(`Calendario de festivos: ${lugaresTxt[0]}`);
    const [vencimiento, saltados] = R.siguienteHabil(nominal);
    if (saltados.length) {
      paso(`Ese día no es hábil (${resumenExcluidos(saltados)}); el plazo pasa al inmediato hábil siguiente, ` +
        `el ${fechaLarga(vencimiento)}`, norma);
      paso("Son inhábiles los sábados, domingos y festivos, como en la Ley 39/2015, supletoria en lo tributario", N.LGT_7_2);
    }
    if (!lugares.some((l) => l.ccaa)) {
      avisos.push("No se ha indicado comunidad autónoma: solo se descuentan los festivos nacionales.");
    }
    if (!DATOS.oficiales.includes(anio(vencimiento))) {
      avisos.push(`El calendario de festivos de ${anio(vencimiento)} no está verificado con el BOE en esta ` +
        "versión; se usan los datos de la librería holidays.");
    }
    if (!localesConocidos(lugares, anio(vencimiento))) {
      avisos.push(`Faltan los festivos locales de ${anio(vencimiento)}: si el último día es fiesta local, el plazo ` +
        "pasa al siguiente hábil. Indica el municipio o sus fiestas locales.");
    }
    avisos.push("El banco o la sede electrónica pueden tener su propio horario de cargo; no dejes el pago para el último momento.");
    return {
      inicio: notificacion, cantidad: 1, unidad: `pago_${periodo}`, jurisdiccion: "tributario", vencimiento, pasos,
      excluidos: saltados, advertencias: avisos, presentacionHasta: null, normas,
    };
  }

  const api = { calcular, plazoPago, fechaLarga, iso, municipioDatos, JURISDICCIONES, UNIDADES };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  raiz.Plazos = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
