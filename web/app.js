(function () {
  "use strict";

  const D = globalThis.PLAZOS_DATOS;
  const P = globalThis.Plazos;
  const $ = (id) => document.getElementById(id);
  const ANIO_DATOS = String(D.oficiales[D.oficiales.length - 1]);
  let municipiosListos = false;
  const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
    "octubre", "noviembre", "diciembre"];
  const TEXTO_URGENTE = {
    civil: "Actuación urgente (art. 131.2 LEC): agosto cuenta",
    contencioso: "Protección de derechos fundamentales: agosto cuenta",
    social: "Modalidad urgente del art. 43.4 LRJS (despido, vacaciones, conflicto colectivo…)",
  };
  const NOMBRE_UNIDAD = { dias: "días hábiles", dias_naturales: "días naturales", meses: "meses", anios: "años", horas: "horas" };
  const UNA_UNIDAD = { dias: "día hábil", dias_naturales: "día natural", meses: "mes", anios: "año", horas: "hora" };

  // Plazos de duración fija y sin discusión, con su artículo. Solo rellenan la duración: la fecha
  // y el municipio los sigue poniendo quien usa la calculadora.
  const HABITUALES = {
    administrativo: [
      ["Subsanar la solicitud", 10, "dias", "art. 68.1 Ley 39/2015"],
      ["Recurso de alzada", 1, "meses", "art. 122.1 Ley 39/2015"],
      ["Recurso de reposición", 1, "meses", "art. 124.1 Ley 39/2015"],
    ],
    civil: [
      ["Contestar la demanda (ordinario)", 20, "dias", "art. 404.1 LEC"],
      ["Contestar la demanda (verbal)", 10, "dias", "art. 438.1 LEC"],
      ["Oponerse a la ejecución", 10, "dias", "art. 556.1 LEC"],
      ["Recurso de reposición", 5, "dias", "art. 452 LEC"],
      ["Recurso de apelación", 20, "dias", "art. 458.1 LEC"],
    ],
    contencioso: [
      ["Recurso contencioso-administrativo", 2, "meses", "art. 46.1 LJCA"],
      ["Formalizar la demanda", 20, "dias", "art. 52.1 LJCA"],
      ["Recurso de apelación", 15, "dias", "art. 85.1 LJCA"],
    ],
    social: [
      ["Demanda por despido", 20, "dias", "art. 103.1 LRJS", true],
      ["Recurso de reposición", 3, "dias", "art. 187.1 LRJS"],
      ["Anunciar recurso de suplicación", 5, "dias", "art. 194.1 LRJS"],
    ],
  };

  const locales = new Set();
  let ultimo = null;
  let tocado = false;           // hasta que se toca algo, no se enseñan errores
  let habitual = null;          // el plazo habitual elegido (mientras no se cambie la duración)

  // --- Buscador con lista propia (en vez de <select> y <datalist>) ------------
  // Encuentra sin tildes ni mayúsculas, primero lo que empieza por lo escrito, y se maneja con
  // flechas, Intro y Escape. El valor elegido es el de la opción cuyo texto coincide con el campo.
  const normal = (t) => t.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();

  class Buscador {
    constructor(input, { max = 60 } = {}) {
      this.input = input;
      this.max = max;
      this.items = [];
      this.vistos = [];
      this.porTexto = new Map();
      this.activo = -1;
      this.lista = document.createElement("ul");
      this.lista.className = "lista-combo";
      this.lista.id = input.id + "-lista";
      this.lista.setAttribute("role", "listbox");
      this.lista.hidden = true;
      input.setAttribute("aria-controls", this.lista.id);
      input.after(this.lista);
      input.addEventListener("input", () => this.abrir());
      input.addEventListener("focus", () => this.abrir());
      input.addEventListener("blur", () => setTimeout(() => this.cerrar(), 120));
      input.addEventListener("keydown", (e) => this.tecla(e));
    }

    poner(items) {
      this.items = items.map(([valor, texto]) => ({ valor, texto, clave: normal(texto) }));
      this.porTexto = new Map(this.items.map((i) => [i.clave, i.valor]));
    }

    get valor() { return this.porTexto.get(normal(this.input.value)) ?? ""; }

    set valor(v) {
      const it = this.items.find((i) => i.valor === v);
      this.input.value = it ? it.texto : "";
    }

    candidatos() {
      const q = normal(this.input.value);
      if (!q) return this.items.slice(0, this.max);
      // primero el nombre exacto, luego los que empiezan por lo escrito, luego los que tienen
      // una palabra que empieza así («Cáceres» antes que «Abadía (Cáceres)»), y al final el resto
      const grupos = [[], [], [], []];
      for (const i of this.items) {
        const k = i.clave;
        const nombre = k.replace(/ \(.*\)$/, "");
        if (nombre === q || k === q) grupos[0].push(i);
        else if (k.startsWith(q)) grupos[1].push(i);
        else if (k.includes(" " + q) || k.includes("(" + q) || k.includes("-" + q)) grupos[2].push(i);
        else if (k.includes(q)) grupos[3].push(i);
      }
      return grupos.flat().slice(0, this.max);
    }

    abrir() {
      const c = this.candidatos();
      this.vistos = c;
      this.activo = -1;
      this.lista.replaceChildren(...c.map((i, n) => {
        const li = document.createElement("li");
        li.id = `${this.lista.id}-${n}`;
        li.setAttribute("role", "option");
        li.textContent = i.texto;
        li.addEventListener("mousedown", (e) => { e.preventDefault(); this.elegir(i); });
        return li;
      }));
      if (!c.length && normal(this.input.value)) {
        const li = document.createElement("li");
        li.className = "sin";
        li.textContent = "Sin resultados";
        this.lista.append(li);
      }
      this.lista.hidden = !this.lista.children.length;
      this.input.setAttribute("aria-expanded", String(!this.lista.hidden));
    }

    cerrar() {
      this.lista.hidden = true;
      this.input.setAttribute("aria-expanded", "false");
      this.input.removeAttribute("aria-activedescendant");
    }

    marcar(n) {
      const lis = [...this.lista.querySelectorAll('[role="option"]')];
      if (!lis.length) return;
      this.activo = (n + lis.length) % lis.length;
      lis.forEach((li, i) => li.setAttribute("aria-selected", String(i === this.activo)));
      lis[this.activo].scrollIntoView({ block: "nearest" });
      this.input.setAttribute("aria-activedescendant", lis[this.activo].id);
    }

    tecla(e) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        if (this.lista.hidden) this.abrir();
        this.marcar(this.activo + (e.key === "ArrowDown" ? 1 : -1));
        e.preventDefault();
      } else if (e.key === "Enter" && !this.lista.hidden && this.activo >= 0) {
        this.elegir(this.vistos[this.activo]);
        e.preventDefault();
      } else if (e.key === "Escape") {
        this.cerrar();
      }
    }

    elegir(i) {
      this.input.value = i.texto;
      this.cerrar();
      this.input.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  const bMunicipio = new Buscador($("municipio"), { max: 50 });
  const bCcaa = new Buscador($("ccaa"));
  const bIsla = new Buscador($("isla"));
  const bSede = new Buscador($("ccaa-sede"));

  function rellenar() {
    const cc = Object.keys(D.ccaa).sort((a, b) => D.ccaa[a].localeCompare(D.ccaa[b], "es")).map((c) => [c, D.ccaa[c]]);
    bCcaa.poner(cc);
    bSede.poner(cc);
    bIsla.poner(Object.keys(D.insulares[ANIO_DATOS]).sort((a, b) => a.localeCompare(b, "es")).map((i) => [i, i]));
    $("version").textContent = `plazos ${D.version}`;
  }

  function cargarMunicipios(M) {
    globalThis.PLAZOS_MUNICIPIOS = M;
    const repetidos = new Map();
    for (const f of M.municipios) repetidos.set(f[1], (repetidos.get(f[1]) || 0) + 1);
    const items = M.municipios.map((f) => [f[0], repetidos.get(f[1]) > 1 || f[1] !== f[3] ? `${f[1]} (${f[3]})` : f[1]]);
    items.sort((a, b) => a[1].localeCompare(b[1], "es"));
    bMunicipio.poner(items);
    municipiosListos = true;
  }

  const radio = (nombre) => document.querySelector(`input[name="${nombre}"]:checked`).value;
  const marcarRadio = (nombre, valor) => {
    const r = document.querySelector(`input[name="${nombre}"][value="${CSS.escape(valor)}"]`);
    if (r) r.checked = true;
  };
  const ineElegido = () => bMunicipio.valor || null;

  // --- Estado <-> formulario <-> URL -----------------------------------------
  function leer() {
    const jurisdiccion = radio("jurisdiccion");
    const municipio = ineElegido();
    const lugar = (e) => {
      if (municipio) {
        e.municipio = municipio;
      } else {
        e.ccaa = bCcaa.valor || null;
        if (e.ccaa === "CN" && bIsla.valor) e.isla = bIsla.valor;
        e.festivosLocales = [...locales].sort();
      }
      return e;
    };
    if (jurisdiccion === "tributario") {
      return lugar({ jurisdiccion, pago: true, inicio: $("inicio").value, notificacion: $("inicio").value,
        periodo: radio("periodo") });
    }
    const estado = lugar({
      jurisdiccion,
      inicio: $("inicio").value,
      cantidad: $("cantidad").value === "" ? null : Number($("cantidad").value),
      unidad: radio("unidad"),
      urgente: jurisdiccion !== "administrativo" && $("urgente").checked,
    });
    if (estado.unidad === "horas") estado.hora = $("hora").value;
    if (jurisdiccion === "administrativo" && $("campo-sede").open && bSede.valor) {
      estado.lugares = [{ ccaa: bSede.valor }];
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
    marcarRadio("jurisdiccion", p.get("j") || "administrativo");
    $("inicio").value = p.get("i");
    $("cantidad").value = p.get("n") || "";
    marcarRadio("unidad", p.get("u") || "dias");
    if (p.has("h")) $("hora").value = p.get("h");
    if (p.has("pp")) marcarRadio("periodo", p.get("pp"));
    bMunicipio.valor = p.get("m") || "";
    if (!bMunicipio.valor) {
      bCcaa.valor = p.get("c") || "";
      bIsla.valor = p.get("isla") || "";
      (p.get("l") || "").split(",").filter(Boolean).forEach((f) => locales.add(f));
      $("otro-lugar").dataset.abierto = p.has("c") || p.has("l") ? "1" : "";
    }
    $("urgente").checked = p.get("urg") === "1";
    if (p.has("sede")) { $("campo-sede").open = true; bSede.valor = p.get("sede"); }
    tocado = true;
    return true;
  }

  // --- Interfaz dependiente de las opciones ----------------------------------
  function pintarHabituales(j) {
    const lista = HABITUALES[j] || [];
    $("campo-habituales").hidden = !lista.length;
    $("habituales").replaceChildren(...lista.map(([texto, n, u, cita, urgente]) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      const clave = `${j}|${texto}`;
      const sigue = habitual === clave && $("cantidad").value === String(n) && radio("unidad") === u;
      b.setAttribute("aria-pressed", String(sigue));
      const t = document.createElement("span");
      t.className = "chip-nombre";
      t.textContent = texto;
      const s = document.createElement("span");
      s.className = "chip-dato";
      s.textContent = `${n} ${n === 1 ? UNA_UNIDAD[u] : NOMBRE_UNIDAD[u]}`;
      const c = document.createElement("span");
      c.className = "chip-dato";
      c.textContent = cita;
      b.append(t, s, c);
      b.addEventListener("click", () => {
        habitual = clave;
        $("cantidad").value = String(n);
        marcarRadio("unidad", u);
        if (j !== "administrativo") $("urgente").checked = Boolean(urgente);
        tocado = true;
        actualizar();
        if (!$("inicio").value) $("inicio").focus();
      });
      return b;
    }));
  }

  function ajustar() {
    const j = radio("jurisdiccion");
    const tributario = j === "tributario";
    const judicial = j !== "administrativo" && !tributario;
    for (const u of ["dias_naturales", "horas"]) {
      const r = document.querySelector(`input[name="unidad"][value="${u}"]`);
      r.disabled = judicial;
      r.closest("label").hidden = judicial;
      if (judicial && r.checked) marcarRadio("unidad", "dias");
    }
    document.querySelector(".unidades").classList.toggle("tres", judicial);
    $("campo-duracion").hidden = tributario;
    $("campo-cantidad").hidden = tributario;
    $("campo-periodo").hidden = !tributario;
    $("campo-hora").hidden = tributario || radio("unidad") !== "horas";
    $("etiqueta-inicio").textContent = tributario ? "Día en que recibiste la notificación" : "Día de la notificación";
    $("campo-urgente").hidden = !judicial;
    if (judicial) $("texto-urgente").textContent = TEXTO_URGENTE[j];
    $("campo-sede").hidden = j !== "administrativo";
    pintarHabituales(j);

    const ine = ineElegido();
    const escrito = $("municipio").value.trim();
    const otro = municipiosListos && !ine && (escrito !== "" || $("otro-lugar").dataset.abierto === "1");
    $("otro-lugar").hidden = !otro;
    const ayuda = $("ayuda-municipio");
    ayuda.replaceChildren();
    if (!municipiosListos) {
      ayuda.textContent = "Cargando las fiestas locales de los municipios…";
    } else if (ine) {
      const m = P.municipioDatos(ine, Number(D.aniosMunicipios[D.aniosMunicipios.length - 1]));
      const dias = m.dias.map((x) => `${x.slice(8, 10)}/${x.slice(5, 7)}`).join(" y ") || "sin fiestas comunes a todo el término";
      if (m.estado) {
        ayuda.textContent = `Sin fiestas locales en ${m.anio}: ` +
          (m.estado === "no_comunicado" ? "el boletín recoge que el ayuntamiento no las comunicó." :
            "el municipio no figura en el boletín oficial de su provincia.") + ` Fuente: ${m.fuente.texto}.`;
      } else {
        ayuda.textContent = `Fiestas locales de ${m.anio}: ${dias}` +
          (m.parciales.length ? `, y otras en ${m.parciales.length === 1 ? "una zona" : "algunas zonas"} del municipio.` : ".") +
          (m.aviso ? ` Ojo: ${m.aviso}.` : "") + ` Fuente: ${m.fuente.texto}.`;
      }
    } else if (escrito) {
      ayuda.textContent = "No encuentro ese municipio: elige uno de la lista o indica abajo la comunidad y sus fiestas locales.";
    } else {
      ayuda.append("Sin municipio solo se descuentan los festivos nacionales. ");
      const b = document.createElement("button");
      b.type = "button";
      b.className = "enlace";
      b.textContent = $("otro-lugar").dataset.abierto === "1" ? "Ocultar comunidad y fiestas" : "Mi municipio no aparece";
      b.addEventListener("click", () => {
        $("otro-lugar").dataset.abierto = $("otro-lugar").dataset.abierto === "1" ? "" : "1";
        actualizar();
      });
      ayuda.append(b);
    }
    $("campo-isla").hidden = !(otro && bCcaa.valor === "CN");
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

  function mostrarResultado(si) {
    $("vacio").hidden = si;
    $("vencimiento").hidden = !si;
    document.querySelectorAll(".con-resultado").forEach((el) => { el.hidden = !si; });
  }

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
    const falta = !e.inicio || (!e.pago && e.cantidad === null) || (e.unidad === "horas" && !e.hora);
    if (falta) {
      // todavía no hay nada que calcular: la explicación de qué rellenar, sin errores
      ultimo = null;
      error.hidden = true;
      mostrarResultado(false);
      if (location.hash) history.replaceState(null, "", location.pathname);
      return;
    }
    try {
      if (e.inicio < "2025-01-01" || e.inicio > "2028-12-31") throw new Error("La fecha tiene que estar entre 2025 y 2028.");
      if (!e.pago) {
        if (!(e.cantidad >= 1) || !Number.isInteger(e.cantidad)) throw new Error("La duración tiene que ser un número entero mayor que cero.");
        if (e.unidad === "dias" && e.cantidad > 365) throw new Error("Como mucho, 365 días hábiles.");
        if (e.unidad === "horas" && e.cantidad > 24) throw new Error("Un plazo por horas no puede pasar de 24 horas.");
        if (!["dias", "horas"].includes(e.unidad) && e.cantidad > 36) throw new Error("Como mucho, 36 meses o 3 años.");
      }
      ultimo = e.pago ? P.plazoPago(e) : P.calcular(e);
      error.hidden = true;
      mostrarResultado(true);
      pintar(ultimo);
      history.replaceState(null, "", aUrl(e));
    } catch (err) {
      ultimo = null;
      error.textContent = err.message;
      error.hidden = !tocado;
      mostrarResultado(false);
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
        : "Vence plazo (" + r.cantidad + " " + NOMBRE_UNIDAD[radio("unidad")] + ")")}`),
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

  // --- Arranque: el formulario empieza vacío (salvo que el enlace traiga un cálculo) ---
  rellenar();
  ajustar();
  mostrarResultado(false);
  fetch("municipios.json")
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.statusText))))
    .then(cargarMunicipios)
    .catch(() => { municipiosListos = true; })  // sin fiestas locales precargadas: se piden a mano
    .finally(() => {
      desdeUrl();
      actualizar();
    });
  const alCambiar = (ev) => {
    if (ev.target.id !== "nuevo-local") tocado = true;
    actualizar();
  };
  $("formulario").addEventListener("input", alCambiar);
  $("formulario").addEventListener("change", alCambiar);
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
