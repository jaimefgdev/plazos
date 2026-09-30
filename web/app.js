(function () {
  "use strict";

  const D = globalThis.PLAZOS_DATOS;
  const P = globalThis.Plazos;
  const $ = (id) => document.getElementById(id);
  const ANIO_DATOS = String(D.oficiales[D.oficiales.length - 1]);
  // Etiqueta visible en el buscador («Nombre (Provincia)») -> código INE, y al revés.
  const ETIQUETA_A_INE = new Map();
  const INE_A_ETIQUETA = new Map();
  let municipiosListos = false;
  const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
    "octubre", "noviembre", "diciembre"];
  const TEXTO_URGENTE = {
    civil: "Actuación urgente (art. 131.2 LEC): agosto cuenta",
    contencioso: "Protección de derechos fundamentales: agosto cuenta",
    social: "Modalidad urgente del art. 43.4 LRJS (despido, vacaciones, conflicto colectivo…)",
  };

  const locales = new Set();
  let ultimo = null;

  // --- Opciones de los desplegables ------------------------------------------
  function opcion(valor, texto) {
    const o = document.createElement("option");
    o.value = valor;
    o.textContent = texto;
    return o;
  }

  function rellenar() {
    const nombres = Object.keys(D.ccaa).sort((a, b) => D.ccaa[a].localeCompare(D.ccaa[b], "es"));
    $("ccaa").append(opcion("", "Ninguna (solo festivos nacionales)"));
    $("ccaa-sede").append(opcion("", "La misma que la mía"));
    for (const cc of nombres) {
      $("ccaa").append(opcion(cc, D.ccaa[cc]));
      $("ccaa-sede").append(opcion(cc, D.ccaa[cc]));
    }
    $("isla").append(opcion("", "Elige isla"));
    Object.keys(D.insulares[ANIO_DATOS]).sort((a, b) => a.localeCompare(b, "es")).forEach((i) => $("isla").append(opcion(i, i)));
    $("version").textContent = `plazos ${D.version}`;
  }

  function cargarMunicipios(M) {
    globalThis.PLAZOS_MUNICIPIOS = M;
    const repetidos = new Map();
    for (const f of M.municipios) repetidos.set(f[1], (repetidos.get(f[1]) || 0) + 1);
    const lista = $("lista-municipios");
    const opciones = [];
    for (const f of M.municipios) {
      const etiqueta = repetidos.get(f[1]) > 1 || f[1] !== f[3] ? `${f[1]} (${f[3]})` : f[1];
      ETIQUETA_A_INE.set(etiqueta, f[0]);
      INE_A_ETIQUETA.set(f[0], etiqueta);
      opciones.push(etiqueta);
    }
    opciones.sort((a, b) => a.localeCompare(b, "es"));
    lista.replaceChildren(...opciones.map((e) => { const o = document.createElement("option"); o.value = e; return o; }));
    municipiosListos = true;
  }

  const ineElegido = () => ETIQUETA_A_INE.get($("municipio").value.trim()) || null;

  // --- Estado <-> formulario <-> URL -----------------------------------------
  function leer() {
    const jurisdiccion = document.querySelector('input[name="jurisdiccion"]:checked').value;
    const municipio = ineElegido();
    if (jurisdiccion === "tributario") {
      const e = { jurisdiccion, pago: true, inicio: $("inicio").value, notificacion: $("inicio").value,
        periodo: $("periodo").value };
      const ine = ineElegido();
      if (ine) {
        e.municipio = ine;
      } else {
        e.ccaa = $("ccaa").value || null;
        if (e.ccaa === "CN" && $("isla").value) e.isla = $("isla").value;
        e.festivosLocales = [...locales].sort();
      }
      return e;
    }
    const estado = {
      jurisdiccion,
      inicio: $("inicio").value,
      cantidad: Number($("cantidad").value),
      unidad: $("unidad").value,
      urgente: jurisdiccion !== "administrativo" && $("urgente").checked,
    };
    if (estado.unidad === "horas") estado.hora = $("hora").value;
    if (!municipio) {
      estado.ccaa = $("ccaa").value || null;
      if (estado.ccaa === "CN" && $("isla").value) estado.isla = $("isla").value;
      estado.festivosLocales = [...locales].sort();
    } else {
      estado.municipio = municipio;
    }
    if (jurisdiccion === "administrativo" && $("campo-sede").open && $("ccaa-sede").value) {
      estado.lugares = [{ ccaa: $("ccaa-sede").value }];
    }
    return estado;
  }

  function aUrl(e) {
    const p = e.pago
      ? new URLSearchParams({ j: e.jurisdiccion, i: e.inicio, pp: e.periodo })
      : new URLSearchParams({ j: e.jurisdiccion, i: e.inicio, n: e.cantidad, u: e.unidad });
    if (e.hora) p.set("h", e.hora);
    if (e.municipio) p.set("m", e.municipio);
    if (e.ccaa) p.set("c", e.ccaa);
    if (e.isla) p.set("isla", e.isla);
    if (e.festivosLocales && e.festivosLocales.length) p.set("l", e.festivosLocales.join(","));
    if (e.urgente) p.set("urg", "1");
    if (e.lugares) p.set("sede", e.lugares[0].ccaa);
    return "#" + p.toString();
  }

  function desdeUrl() {
    const p = new URLSearchParams(location.hash.slice(1));
    if (!p.has("i")) return false;
    locales.clear();
    const j = p.get("j") || "administrativo";
    const radio = document.querySelector(`input[name="jurisdiccion"][value="${CSS.escape(j)}"]`);
    if (radio) radio.checked = true;
    $("inicio").value = p.get("i");
    $("cantidad").value = p.get("n") || "10";
    $("unidad").value = p.get("u") || "dias";
    if (p.has("h")) $("hora").value = p.get("h");
    if (p.has("pp")) $("periodo").value = p.get("pp");
    if (p.has("m") && INE_A_ETIQUETA.has(p.get("m"))) {
      $("municipio").value = INE_A_ETIQUETA.get(p.get("m"));
    } else {
      $("municipio").value = "";
      $("ccaa").value = p.get("c") || "";
      $("isla").value = p.get("isla") || "";
      (p.get("l") || "").split(",").filter(Boolean).forEach((f) => locales.add(f));
    }
    $("urgente").checked = p.get("urg") === "1";
    if (p.has("sede")) { $("campo-sede").open = true; $("ccaa-sede").value = p.get("sede"); }
    return true;
  }

  // --- Interfaz dependiente de las opciones ----------------------------------
  function ajustar() {
    const j = document.querySelector('input[name="jurisdiccion"]:checked').value;
    const tributario = j === "tributario";
    const judicial = j !== "administrativo" && !tributario;
    for (const u of ["dias_naturales", "horas"]) {
      $("unidad").querySelector(`option[value="${u}"]`).disabled = judicial;
      if (judicial && $("unidad").value === u) $("unidad").value = "dias";
    }
    $("campo-duracion").hidden = tributario;
    $("campo-periodo").hidden = !tributario;
    $("campo-hora").hidden = tributario || $("unidad").value !== "horas";
    $("etiqueta-inicio").textContent = tributario ? "Día en que recibiste la notificación" : "Día de la notificación";
    $("campo-urgente").hidden = !judicial;
    if (judicial) $("texto-urgente").textContent = TEXTO_URGENTE[j];
    $("campo-sede").hidden = j !== "administrativo";
    const ine = ineElegido();
    const otro = municipiosListos && !ine;
    $("otro-lugar").hidden = !otro;
    const ayuda = $("ayuda-municipio");
    if (!municipiosListos) {
      ayuda.textContent = "Cargando las fiestas locales de los municipios…";
    } else if (ine) {
      const m = P.municipioDatos(ine, Number(D.aniosMunicipios[D.aniosMunicipios.length - 1]));
      const dias = m.dias.map((x) => `${x.slice(8, 10)}/${x.slice(5, 7)}`).join(" y ") || "sin fiestas comunes a todo el término";
      ayuda.textContent = `Fiestas locales de ${m.anio}: ${dias}` +
        (m.parciales.length ? `, y otras en ${m.parciales.length === 1 ? "una zona" : "algunas zonas"} del municipio.` : ".") +
        ` Fuente: ${m.fuente.texto}.`;
    } else {
      ayuda.textContent = $("municipio").value.trim()
        ? "No encuentro ese municipio en la lista: elige la comunidad y añade sus fiestas locales."
        : "Escribe y elige tu municipio de la lista. Si no aparece, indica la comunidad y sus fiestas locales.";
    }
    $("campo-isla").hidden = !(otro && $("ccaa").value === "CN");
    const fichas = $("locales");
    fichas.replaceChildren(...[...locales].sort().map((f) => {
      const li = document.createElement("li");
      const [a, m, d] = f.split("-");
      li.append(`${d}/${m}/${a}`);
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = "×";
      b.setAttribute("aria-label", `Quitar ${d}/${m}/${a}`);
      b.addEventListener("click", () => { locales.delete(f); actualizar(); });
      li.append(b);
      return li;
    }));
  }

  // --- Resultado ---------------------------------------------------------------
  const fechaTxt = (f) => P.fechaLarga(f);
  const corta = (iso) => { const [a, m, d] = iso.split("-"); return `${d}/${m}/${a}`; };

  function pintarPasos(r) {
    $("pasos").replaceChildren(...r.pasos.map((p) => {
      const li = document.createElement("li");
      li.append(p.texto);
      if (p.norma) {
        const a = document.createElement("a");
        a.className = "norma";
        a.href = p.norma.url;
        a.target = "_blank";
        a.rel = "noopener";
        a.textContent = p.norma.cita;
        li.append(" ", a);
      }
      return li;
    }));
    $("avisos").replaceChildren(...r.advertencias.map((t) => {
      const li = document.createElement("li");
      li.textContent = t;
      return li;
    }));
  }

  function pintarCalendario(r) {
    const cont = $("calendario");
    const excluidos = new Map(r.excluidos.map((e) => [P.iso(e.fecha), e.motivo]));
    const inicio = P.iso(r.inicio);
    const fin = P.iso(r.vencimiento);
    const gracia = r.presentacionHasta ? r.presentacionHasta.slice(0, 10) : null;
    const ultimoDia = gracia || fin;
    const numeros = new Map();
    if (r.unidad === "dias") {
      let n = 0;
      for (let d = new Date(r.inicio.getTime() + 86400000); P.iso(d) <= fin; d = new Date(d.getTime() + 86400000)) {
        if (!excluidos.has(P.iso(d))) numeros.set(P.iso(d), ++n);
      }
    }
    const meses = [];
    let a = r.inicio.getUTCFullYear();
    let m = r.inicio.getUTCMonth();
    const [aFin, mFin] = ultimoDia.split("-").map(Number);
    while (a < aFin || (a === aFin && m <= mFin - 1)) {
      meses.push([a, m]);
      if (++m === 12) { m = 0; a++; }
    }
    let visibles = meses;
    const piezas = [];
    const porMeses = r.unidad === "meses" || r.unidad === "anios" || r.jurisdiccion === "tributario";
    if (meses.length > 4 || (porMeses && meses.length > 2)) {
      const finales = meses.slice(-2).filter(([a2, m2]) => `${a2}-${String(m2 + 1).padStart(2, "0")}` >= fin.slice(0, 7));
      visibles = [meses[0], ...finales];
      const p = document.createElement("p");
      p.className = "calendario-resumen";
      p.textContent = porMeses
        ? "En los plazos por meses se cuenta de fecha a fecha: se muestran el mes de la notificación y el del vencimiento."
        : `Se muestran el mes de la notificación y los dos últimos (${meses.length} meses en total).`;
      piezas.push(p);
    }
    const rejilla = document.createElement("div");
    rejilla.className = "calendario";
    rejilla.style.display = "contents";
    for (const [anio, mes] of visibles) {
      const bloque = document.createElement("div");
      bloque.className = "mes";
      const h = document.createElement("h3");
      h.textContent = `${MESES[mes]} ${anio}`;
      const cab = document.createElement("div");
      cab.className = "semana";
      "LMXJVSD".split("").forEach((l) => { const s = document.createElement("span"); s.textContent = l; cab.append(s); });
      const dias = document.createElement("div");
      dias.className = "dias";
      const primero = (new Date(Date.UTC(anio, mes, 1)).getUTCDay() + 6) % 7;
      for (let i = 0; i < primero; i++) { const v = document.createElement("span"); v.className = "dia fuera"; dias.append(v); }
      const total = new Date(Date.UTC(anio, mes + 1, 0)).getUTCDate();
      for (let d = 1; d <= total; d++) {
        const iso = `${anio}-${String(mes + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
        const motivo = excluidos.get(iso);
        const el = document.createElement(motivo ? "button" : "span");
        el.className = "dia";
        el.textContent = d;
        if (iso === inicio) { el.classList.add("notificacion"); el.title = "Notificación"; }
        if (numeros.has(iso)) { el.classList.add("cuenta"); el.dataset.n = numeros.get(iso); }
        if (motivo) {
          el.type = "button";
          el.classList.add("no");
          if (!/^(sábado|domingo)$/.test(motivo)) el.classList.add("festivo");
          el.setAttribute("aria-label", `${d}: no cuenta, ${motivo}`);
          el.setAttribute("aria-pressed", "false");
          el.addEventListener("click", () => {
            cont.querySelectorAll('.dia[aria-pressed="true"]').forEach((x) => x.setAttribute("aria-pressed", "false"));
            el.setAttribute("aria-pressed", "true");
            const t = $("detalle-dia");
            t.replaceChildren();
            const s = document.createElement("strong");
            s.textContent = corta(iso);
            t.append(s, ` no cuenta: ${motivo}.`);
          });
        }
        if (iso === fin) { el.classList.add("fin"); el.title = "Vencimiento"; }
        if (iso === gracia) { el.classList.add("gracia"); el.title = "Hasta las 15:00 se puede presentar"; }
        dias.append(el);
      }
      bloque.append(h, cab, dias);
      rejilla.append(bloque);
    }
    piezas.push(rejilla);
    cont.replaceChildren(...piezas);
    $("detalle-dia").textContent = r.excluidos.length ? "Toca un día tachado para ver por qué no cuenta." : "";
  }

  function pintar(r) {
    $("fecha-vence").textContent = fechaTxt(r.vencimiento);
    const hasta = $("hasta");
    hasta.replaceChildren();
    if (r.jurisdiccion === "tributario") {
      const s = document.createElement("strong");
      s.textContent = "hasta ese día";
      hasta.append(`Puedes pagar en periodo ${r.unidad === "pago_voluntario" ? "voluntario" : "de apremio"} `, s,
        r.unidad === "pago_voluntario" ? " (art. 62.2 LGT)." : " (art. 62.5 LGT).");
    } else if (r.unidad === "horas") {
      const s = document.createElement("strong");
      s.textContent = `a las ${horaFin(r)}`;
      hasta.append("El plazo acaba ", s, " de ese día (art. 30.1 Ley 39/2015).");
    } else if (r.presentacionHasta) {
      const f = new Date(r.presentacionHasta.slice(0, 10) + "T00:00:00Z");
      const s = document.createElement("strong");
      s.textContent = `hasta las 15:00 del ${fechaTxt(f)}`;
      hasta.append("Puedes presentar el escrito ", s, r.jurisdiccion === "social" ? " (art. 45.1 LRJS)." : " (art. 135.5 LEC).");
    } else {
      const s = document.createElement("strong");
      s.textContent = "hasta las 23:59:59";
      hasta.append("En el registro electrónico, ", s, " de ese día (art. 31.2 Ley 39/2015).");
    }
    pintarCalendario(r);
    pintarPasos(r);
  }

  // «2026-10-06T00:00» es el final (24:00) del día anterior.
  const horaFin = (r) => (r.presentacionHasta.endsWith("T00:00") ? "24:00" : r.presentacionHasta.slice(11));

  function explicacion(r) {
    const lineas = [`Vence el ${fechaTxt(r.vencimiento)}.`];
    if (r.unidad === "horas") {
      lineas.push(`Último momento para presentar: ${fechaTxt(r.vencimiento)} a las ${horaFin(r)}.`);
    } else if (r.presentacionHasta) {
      lineas.push(`Último momento para presentar: ${fechaTxt(new Date(r.presentacionHasta.slice(0, 10) + "T00:00:00Z"))} a las 15:00.`);
    }
    lineas.push("");
    r.pasos.forEach((p, i) => lineas.push(`${i + 1}. ${p.texto}${p.norma ? ` (${p.norma.cita})` : ""}`));
    if (r.advertencias.length) { lineas.push(""); r.advertencias.forEach((a) => lineas.push(`Aviso: ${a}`)); }
    lineas.push("", `Calculado con ${location.origin}${location.pathname}${aUrl(leer())}`);
    return lineas.join("\n");
  }

  function actualizar() {
    ajustar();
    if (!municipiosListos) return;
    const e = leer();
    const error = $("error");
    try {
      if (!e.inicio) throw new Error("Indica el día de la notificación.");
      if (e.inicio < "2025-01-01" || e.inicio > "2028-12-31") throw new Error("La fecha tiene que estar entre 2025 y 2028.");
      if (!e.pago) {
        if (!(e.cantidad >= 1)) throw new Error("La duración tiene que ser un número mayor que cero.");
        if (e.unidad === "dias" && e.cantidad > 365) throw new Error("Como mucho, 365 días hábiles.");
        if (e.unidad === "horas" && e.cantidad > 24) throw new Error("Un plazo por horas no puede pasar de 24 horas.");
        if (!["dias", "horas"].includes(e.unidad) && e.cantidad > 36) throw new Error("Como mucho, 36 meses o 3 años.");
      }
      ultimo = e.pago ? P.plazoPago(e) : P.calcular(e);
      error.hidden = true;
      pintar(ultimo);
      history.replaceState(null, "", aUrl(e));
    } catch (err) {
      error.textContent = err.message;
      error.hidden = false;
    }
  }

  // --- Acciones ---------------------------------------------------------------
  function avisar(texto) {
    const t = document.createElement("div");
    t.className = "aviso-copiado";
    t.setAttribute("role", "status");
    t.textContent = texto;
    document.body.append(t);
    setTimeout(() => t.remove(), 1800);
  }

  async function copiar(texto, hecho) {
    try { await navigator.clipboard.writeText(texto); avisar(hecho); } catch { avisar("No se ha podido copiar"); }
  }

  function ics(r) {
    const compacto = (iso) => iso.replaceAll("-", "");
    const fin = P.iso(r.vencimiento);
    const siguiente = P.iso(new Date(r.vencimiento.getTime() + 86400000));
    const escapar = (t) => t.replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\n/g, "\\n");
    const plegar = (l) => l.match(/.{1,73}/gu).join("\r\n ");
    const texto = [
      "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//jaimefgdev//plazos//ES", "CALSCALE:GREGORIAN", "BEGIN:VEVENT",
      `UID:${compacto(fin)}-${Date.now()}@jaimefgdev.com`,
      `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, "").slice(0, 15)}Z`,
      `DTSTART;VALUE=DATE:${compacto(fin)}`, `DTEND;VALUE=DATE:${compacto(siguiente)}`,
      plegar(`SUMMARY:${escapar(r.jurisdiccion === "tributario" ? "Último día para pagar a Hacienda"
        : "Vence plazo (" + r.cantidad + " " + $("unidad").selectedOptions[0].text + ")")}`),
      plegar(`DESCRIPTION:${escapar(explicacion(r))}`),
      "BEGIN:VALARM", "TRIGGER:-P2D", "ACTION:DISPLAY", "DESCRIPTION:Vence un plazo", "END:VALARM",
      "END:VEVENT", "END:VCALENDAR", "",
    ].join("\r\n");
    const url = URL.createObjectURL(new Blob([texto], { type: "text/calendar;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `plazo-${fin}.ics`;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  // --- Arranque ---------------------------------------------------------------
  rellenar();
  const hoy = new Date();
  const hoyIso = new Date(Date.UTC(hoy.getFullYear(), hoy.getMonth(), hoy.getDate())).toISOString().slice(0, 10);
  $("inicio").value = hoyIso < "2025-01-01" || hoyIso > "2028-12-31" ? "2026-07-20" : hoyIso;
  ajustar();
  fetch("municipios.json")
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.statusText))))
    .then(cargarMunicipios)
    .catch(() => { municipiosListos = true; })  // sin fiestas locales precargadas: se piden a mano
    .finally(() => {
      if (!desdeUrl()) $("municipio").value = INE_A_ETIQUETA.get("28079") || "";
      actualizar();
    });
  $("formulario").addEventListener("input", actualizar);
  $("formulario").addEventListener("change", actualizar);
  $("campo-sede").addEventListener("toggle", actualizar);
  $("formulario").addEventListener("submit", (ev) => ev.preventDefault());
  $("anadir-local").addEventListener("click", () => {
    const v = $("nuevo-local").value;
    if (v) { locales.add(v); $("nuevo-local").value = ""; actualizar(); }
  });
  $("copiar").addEventListener("click", () => ultimo && copiar(explicacion(ultimo), "Explicación copiada"));
  $("enlace").addEventListener("click", () => copiar(location.href, "Enlace copiado"));
  $("ics").addEventListener("click", () => ultimo && ics(ultimo));
  window.addEventListener("hashchange", () => { if (municipiosListos && desdeUrl()) actualizar(); });
})();
