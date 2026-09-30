// Motor de cómputo de «plazos» para el navegador. Es una traducción literal de
// src/plazos/computo.py; tests/test_web.py comprueba que ambos dan lo mismo.
(function (raiz) {
  "use strict";

  const DATOS = raiz.PLAZOS_DATOS;
  const N = DATOS.normas;
  const JURISDICCIONES = ["administrativo", "civil", "contencioso", "social"];
  const UNIDADES = ["dias", "dias_naturales", "meses", "anios"];
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

  function capital(nombre) {
    if (!nombre) return null;
    const clave = normalizar(nombre);
    for (const lista of Object.values(DATOS.capitales)) {
      const c = lista.find((x) => normalizar(x.nombre) === clave);
      if (c) return c;
    }
    return null;
  }

  function fiestasLocales(nombre, a) {
    const lista = DATOS.capitales[String(a)];
    if (!lista || !nombre) return null;
    const c = lista.find((x) => normalizar(x.nombre) === normalizar(nombre));
    return c ? c.dias.map(deIso) : null;
  }

  function crearLugar({ ccaa = null, festivosLocales = [], isla = null, municipio = null } = {}) {
    const c = capital(municipio);
    if (c) {
      if (ccaa && ccaa !== c.ccaa) throw new Error(`${c.nombre} está en ${DATOS.ccaa[c.ccaa]} (${c.ccaa}), no en ${ccaa}`);
      municipio = c.nombre;
      ccaa = c.ccaa;
      if (!isla) isla = c.isla;
    }
    if (ccaa && !DATOS.ccaa[ccaa]) throw new Error(`Comunidad desconocida: ${ccaa}`);
    if (isla && ccaa !== "CN") throw new Error("La isla solo se indica para Canarias");
    const unicos = [...new Set(festivosLocales.map((f) => (typeof f === "string" ? f : iso(f))))].sort();
    return { ccaa, isla, municipio, festivosLocales: unicos.map(deIso) };
  }

  function motivosLugar(f, lugar) {
    const motivos = [];
    const clave = iso(f);
    const anual = DATOS.festivos[String(anio(f))] || {};
    if ((anual.ES || {})[clave]) motivos.push(anual.ES[clave]);
    else if (lugar.ccaa && (anual[lugar.ccaa] || {})[clave]) motivos.push(anual[lugar.ccaa][clave]);
    const insulares = DATOS.insulares[String(anio(f))];
    if (lugar.isla && insulares && insulares[lugar.isla] === clave) motivos.push(`festivo insular en ${lugar.isla}`);
    const oficiales = lugar.municipio ? fiestasLocales(lugar.municipio, anio(f)) : null;
    const esLocal = lugar.festivosLocales.some((x) => iso(x) === clave) ||
      (oficiales && oficiales.some((x) => iso(x) === clave));
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
      (l.municipio && fiestasLocales(l.municipio, a) !== null));
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
    } = opciones;
    if (!JURISDICCIONES.includes(jurisdiccion)) throw new Error(`Jurisdicción desconocida: ${jurisdiccion}`);
    if (!UNIDADES.includes(unidad)) throw new Error(`Unidad desconocida: ${unidad}`);
    if (!Number.isInteger(cantidad) || cantidad < 1) throw new Error("La cantidad debe ser un número entero positivo");
    if (unidad === "dias_naturales" && jurisdiccion !== "administrativo") {
      throw new Error("Los plazos procesales se cuentan en días hábiles, no naturales");
    }
    if (urgente && jurisdiccion === "administrativo") throw new Error("'urgente' solo se aplica a plazos judiciales");

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
      const locales = l.municipio ? fiestasLocales(l.municipio, anio(inicio)) : null;
      const fuente = l.ccaa ? (DATOS.fuentes[String(anio(inicio))] || {})[l.ccaa] : null;
      if (locales && fuente) {
        paso(`Fiestas locales de ${l.municipio} en ${anio(inicio)} (${locales.map(ddmm).join(", ")}), ` +
          `según ${fuente.texto}`);
      }
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

    for (const a of [...new Set([anio(inicio), anio(vencimiento)])].sort()) {
      if (!localesConocidos(lugares, a)) {
        avisos.push(`Faltan los festivos locales de ${a}: si el plazo cruza alguno, vencerá más ` +
          "tarde de lo calculado aquí. Indica el municipio (capitales de provincia) o los días.");
      }
      if (!DATOS.oficiales.includes(a)) {
        avisos.push(`El calendario de festivos de ${a} no está verificado con el BOE en esta ` +
          "versión; se usan los datos de la librería holidays.");
      }
    }

    return {
      inicio, cantidad, unidad, jurisdiccion, vencimiento, pasos, excluidos,
      advertencias: avisos, presentacionHasta: presentacion ? `${iso(presentacion)}T15:00` : null, normas,
    };
  }

  const api = { calcular, fechaLarga, iso, capital, JURISDICCIONES, UNIDADES };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  raiz.Plazos = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
