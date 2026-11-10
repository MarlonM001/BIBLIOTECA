# -*- coding: utf-8 -*-
"""
Bot Scopus SENA
Abre la biblioteca del SENA -> Bases de datos -> baja hasta Scopus -> inicia sesion
-> busca el termino -> abre documentos y los "lee" (scroll pausado).

Los datos llegan por variables de entorno (las pide INICIAR_BOT.bat):
  BOT_USUARIO, BOT_CONTRASENA, BOT_BUSQUEDA, BOT_MINUTOS, BOT_DOCUMENTOS
"""
import os
import random
import subprocess
import sys
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Falta Playwright. Ejecute INICIAR_BOT.bat para instalarlo.")
    input("Enter para salir...")
    sys.exit(1)

CARPETA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_CAPTURAS = os.path.join(CARPETA_BASE, "capturas")
CARPETA_REGISTROS = os.path.join(CARPETA_BASE, "registros")
os.makedirs(CARPETA_CAPTURAS, exist_ok=True)
os.makedirs(CARPETA_REGISTROS, exist_ok=True)
ARCHIVO_LOG = os.path.join(CARPETA_REGISTROS, time.strftime("bot_%Y-%m-%d.log"))

INICIO_URL = "https://biblioteca.sena.edu.co/"
BASES_URL = "https://biblioteca.sena.edu.co/paginas/bases.html"

USUARIO = os.environ.get("BOT_USUARIO", "").strip()
CONTRASENA = os.environ.get("BOT_CONTRASENA", "").strip() or USUARIO
BUSQUEDA = os.environ.get("BOT_BUSQUEDA", "").strip() or "computadores"
try:
    MINUTOS = max(0.5, float(os.environ.get("BOT_MINUTOS", "3").replace(",", ".")))
except ValueError:
    MINUTOS = 3.0
try:
    DOCUMENTOS = max(1, int(os.environ.get("BOT_DOCUMENTOS", "1")))
except ValueError:
    DOCUMENTOS = 1


# ---------------------------------------------------------------- utilidades
def log(msg):
    linea = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(linea, flush=True)
    try:
        with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
    except Exception:
        pass


def pausa(a=0.8, b=2.0):
    time.sleep(random.uniform(a, b))


def primero_visible(page, selectores, timeout=60):
    """Devuelve el primer elemento visible que coincida con alguno de los selectores."""
    fin = time.time() + timeout
    while time.time() < fin:
        for s in selectores:
            try:
                loc = page.locator(s)
                for i in range(min(loc.count(), 8)):
                    el = loc.nth(i)
                    if el.is_visible():
                        return el
            except Exception:
                pass
        time.sleep(0.5)
    return None


def buscar_en_pestanas(context, selectores, timeout=60):
    """Busca el elemento en todas las pestanas abiertas. Devuelve (pestana, elemento)."""
    fin = time.time() + timeout
    while time.time() < fin:
        for pg in reversed(context.pages):
            for s in selectores:
                try:
                    loc = pg.locator(s)
                    for i in range(min(loc.count(), 8)):
                        el = loc.nth(i)
                        if el.is_visible():
                            return pg, el
                except Exception:
                    pass
        time.sleep(0.5)
    return None, None


def visibles(page, selectores, maximo=25):
    """Lista de elementos visibles (sin repetir href) para varios selectores."""
    vistos, salida = set(), []
    for s in selectores:
        try:
            loc = page.locator(s)
            for i in range(min(loc.count(), 60)):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                clave = (el.get_attribute("href") or "") + "|" + (el.inner_text() or "")[:60]
                if clave in vistos:
                    continue
                vistos.add(clave)
                salida.append(el)
                if len(salida) >= maximo:
                    return salida
        except Exception:
            pass
    return salida


def bajar_hasta(page, el, max_pasos=80):
    """Hace scroll con la rueda poco a poco hasta que el elemento quede en pantalla."""
    for _ in range(max_pasos):
        try:
            caja = el.bounding_box()
            alto = page.evaluate("window.innerHeight")
            if caja and 80 < caja["y"] < alto - 120:
                return
            direccion = 1 if (caja is None or caja["y"] >= alto - 120) else -1
        except Exception:
            direccion = 1
        page.mouse.wheel(0, direccion * random.randint(250, 450))
        time.sleep(random.uniform(0.25, 0.6))
    try:
        el.scroll_into_view_if_needed(timeout=5000)
    except Exception:
        pass


def resaltar(el):
    try:
        el.evaluate("e => { e.style.outline='3px solid #ff9800'; e.style.outlineOffset='3px'; }")
    except Exception:
        pass


def clic_seguro(el):
    """Clic normal; si el elemento esta tapado o fuera de pantalla, clic por JavaScript."""
    try:
        el.scroll_into_view_if_needed(timeout=5000)
    except Exception:
        pass
    try:
        el.click(timeout=8000)
        return True
    except Exception:
        pass
    try:
        el.evaluate("e => (e.closest('a') || e).click()")
        return True
    except Exception:
        return False


def clic_y_seguir(context, page, el, espera=15):
    """Hace clic; si se abre una pestana nueva, devuelve esa pestana."""
    antes = len(context.pages)
    clic_seguro(el)
    fin = time.time() + espera
    while time.time() < fin:
        if len(context.pages) > antes:
            nueva = context.pages[-1]
            nueva.bring_to_front()
            try:
                nueva.wait_for_load_state("domcontentloaded", timeout=60000)
            except Exception:
                pass
            return nueva
        time.sleep(0.3)
    try:
        page.wait_for_load_state("domcontentloaded", timeout=60000)
    except Exception:
        pass
    return page


def quitar_cookies(page):
    for s in ["#onetrust-reject-all-handler",
              "button:has-text('Reject all')",
              "button:has-text('Rechazar todas')",
              "button:has-text('Rechazar')",
              "#onetrust-accept-btn-handler",
              "button[aria-label='Close']"]:
        try:
            b = page.locator(s).first
            if b.count() and b.is_visible():
                b.click(timeout=3000)
                log("Aviso de cookies cerrado.")
                pausa(0.5, 1)
                return
        except Exception:
            pass


def abrir_navegador(p):
    opciones = dict(headless=False, slow_mo=60, args=["--start-maximized"])
    for canal, nombre in (("chrome", "Google Chrome"), ("msedge", "Microsoft Edge")):
        try:
            b = p.chromium.launch(channel=canal, **opciones)
            log(f"Navegador: {nombre}")
            return b
        except Exception:
            pass
    log("No se encontro Chrome ni Edge, descargando Chromium (solo la primera vez)...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)
    log("Navegador: Chromium")
    return p.chromium.launch(**opciones)


# ---------------------------------------------------------------- pasos
def ir_a_bases(context, page):
    log("Abriendo la biblioteca del SENA...")
    page.goto(INICIO_URL, wait_until="domcontentloaded", timeout=90000)
    pausa(1.5, 2.5)
    boton = primero_visible(page, ['img[src*="Boton_BD"]',
                                   '.contenedor a[href*="bases.html"] img',
                                   'main a[href*="bases.html"] img'], timeout=15)
    if boton:
        log("Clic en 'Bases de datos'.")
        bajar_hasta(page, boton, max_pasos=15)
        resaltar(boton)
        pausa(0.6, 1.2)
        try:
            page = clic_y_seguir(context, page, boton)
        except Exception as e:
            log(f"No se pudo hacer clic ({e.__class__.__name__}), voy directo.")
    if "bases.html" not in page.url:
        log("Abriendo Bases de datos directamente.")
        page.goto(BASES_URL, wait_until="domcontentloaded", timeout=90000)
    pausa(1.5, 2.5)
    return page


def entrar_a_scopus(context, page):
    log("Bajando hasta Scopus...")
    scopus = page.locator('a[href*="scopus.com"]').first
    scopus.wait_for(state="attached", timeout=30000)
    bajar_hasta(page, scopus)
    resaltar(scopus)
    pausa(1, 2)
    log("Clic en Scopus.")
    return clic_y_seguir(context, page, scopus)


def iniciar_sesion(context, page):
    log("Esperando el formulario de usuario y contrasena...")
    pg, clave = buscar_en_pestanas(context, ['input[type="password"]'], timeout=60)
    if not clave:
        log("No aparecio el login (puede que la sesion ya este abierta). Continuo.")
        return page
    pg.bring_to_front()
    usuario = primero_visible(pg, ['input[name="user"]', 'input[name="username"]',
                                   'input[name="usuario"]', 'input[type="text"]'], timeout=10)
    log("Escribiendo usuario y contrasena...")
    usuario.click()
    usuario.fill("")
    usuario.type(USUARIO, delay=random.randint(70, 140))
    pausa(0.4, 0.9)
    clave.click()
    clave.fill("")
    clave.type(CONTRASENA, delay=random.randint(70, 140))
    pausa(0.6, 1.2)
    boton = primero_visible(pg, ['input[type="submit"]', 'button[type="submit"]',
                                 'button:has-text("Ingresar")', 'input[value*="Ingresar"]'], timeout=5)
    log("Ingresando...")
    if boton:
        clic_seguro(boton)
    else:
        clave.press("Enter")
    try:
        pg.wait_for_load_state("domcontentloaded", timeout=90000)
    except Exception:
        pass
    if pg.locator('input[type="password"]').count() and pg.locator('input[type="password"]').first.is_visible():
        pausa(3, 4)
        if pg.locator('input[type="password"]').count() and pg.locator('input[type="password"]').first.is_visible():
            raise RuntimeError("El login no paso. Revise usuario y contrasena.")
    log("Sesion iniciada.")
    return pg


CAMPO_BUSQUEDA = [
    'input[placeholder*="Search documents" i]',
    'input[aria-label*="Search documents" i]',
    'input[placeholder*="Buscar documentos" i]',
    'input[name="searchterm1"]',
    '#searchterm1',
    'input[data-testid*="search" i][type="text"]',
    'input[type="text"][id*="search" i]',
]

TITULOS = [
    'a[href*="/record/display"]',
    'a[href*="pages/publications"]',
    '[data-testid="results-list-item"] h4 a',
    'table tbody tr td h4 a',
    'table tbody tr td a[href*="eid="]',
]


def buscar(context, page, termino):
    log("Esperando que cargue Scopus...")
    pg, _ = buscar_en_pestanas(context, CAMPO_BUSQUEDA, timeout=90)
    if pg:
        page = pg
        page.bring_to_front()
    try:
        page.wait_for_load_state("networkidle", timeout=60000)
    except Exception:
        pass
    quitar_cookies(page)

    pestana = primero_visible(page, ['button:has-text("Documents")', '[role="tab"]:has-text("Documents")'], timeout=5)
    if pestana:
        try:
            clic_seguro(pestana)
            pausa(0.5, 1)
        except Exception:
            pass

    campo = primero_visible(page, CAMPO_BUSQUEDA, timeout=60)
    if not campo:
        try:
            campo = page.get_by_label("Search documents").first
        except Exception:
            campo = None
    if not campo:
        raise RuntimeError("No encontre el campo de busqueda de Scopus.")

    log(f"Buscando: {termino}")
    resaltar(campo)
    campo.click()
    campo.fill("")
    campo.type(termino, delay=random.randint(90, 170))
    pausa(0.6, 1.2)
    campo.press("Enter")

    if not primero_visible(page, TITULOS, timeout=15):
        boton = primero_visible(page, ['button[type="submit"]:has-text("Search")',
                                       'button:has-text("Search")'], timeout=5)
        if boton:
            clic_seguro(boton)
    if not primero_visible(page, TITULOS, timeout=60):
        raise RuntimeError("No aparecieron resultados.")
    quitar_cookies(page)
    pausa(1.5, 3)
    return page


def leer(page, minutos):
    """Simula lectura: baja poco a poco, pausa, a veces sube un poco y mueve el mouse."""
    log(f"Leyendo el documento durante {minutos:g} minuto(s)...")
    for s in ['button:has-text("Show abstract")', 'button:has-text("View abstract")',
              'button:has-text("Show all information")']:
        try:
            b = page.locator(s).first
            if b.count() and b.is_visible():
                b.click(timeout=3000)
                pausa(0.5, 1)
        except Exception:
            pass

    fin = time.time() + minutos * 60
    ancho = page.evaluate("window.innerWidth")
    alto = page.evaluate("window.innerHeight")
    while time.time() < fin:
        r = random.random()
        if r < 0.75:
            page.mouse.wheel(0, random.randint(90, 260))
        elif r < 0.9:
            page.mouse.wheel(0, -random.randint(60, 180))
        else:
            page.mouse.move(random.randint(int(ancho * 0.2), int(ancho * 0.8)),
                            random.randint(int(alto * 0.2), int(alto * 0.8)),
                            steps=random.randint(8, 25))
        al_final = page.evaluate(
            "window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 60")
        if al_final:
            pausa(3, 6)
            page.mouse.wheel(0, -random.randint(800, 1600))
        time.sleep(random.uniform(2.0, 6.0))
        restante = int(fin - time.time())
        if restante > 0 and restante % 30 < 6:
            log(f"   ...quedan ~{restante} s")
    log("Lectura terminada.")


def abrir_y_leer_documentos(context, resultados, cantidad, minutos):
    usados = set()
    for n in range(1, cantidad + 1):
        titulos = visibles(resultados, TITULOS)
        candidatos = [i for i in range(min(len(titulos), 10)) if i not in usados] or list(range(len(titulos)))
        if not candidatos:
            log("No hay mas documentos en la lista.")
            return
        idx = random.choice(candidatos)
        usados.add(idx)
        el = titulos[idx]
        nombre = (el.inner_text() or "").strip().replace("\n", " ")[:110]
        log(f"Documento {n}/{cantidad}: {nombre}")
        bajar_hasta(resultados, el)
        resaltar(el)
        pausa(1, 2.5)
        doc = clic_y_seguir(context, resultados, el)
        pausa(2, 4)
        quitar_cookies(doc)
        leer(doc, minutos)

        if n < cantidad:
            if doc is not resultados:
                doc.close()
                resultados.bring_to_front()
            else:
                resultados.go_back(wait_until="domcontentloaded")
                primero_visible(resultados, TITULOS, timeout=60)
            pausa(1.5, 3)


# ---------------------------------------------------------------- main
def main():
    if not USUARIO:
        print("Falta el usuario. Ejecute INICIAR_BOT.bat")
        sys.exit(1)
    log(f"Usuario: {USUARIO} | Busqueda: {BUSQUEDA} | Documentos: {DOCUMENTOS} | Minutos c/u: {MINUTOS:g}")

    with sync_playwright() as p:
        navegador = abrir_navegador(p)
        context = navegador.new_context(no_viewport=True, locale="es-CO")
        page = context.new_page()
        try:
            page = ir_a_bases(context, page)
            page = entrar_a_scopus(context, page)
            page = iniciar_sesion(context, page)
            page = buscar(context, page, BUSQUEDA)
            abrir_y_leer_documentos(context, page, DOCUMENTOS, MINUTOS)
            log("Listo. Tarea completada.")
        except Exception as e:
            log(f"ERROR: {e}")
            try:
                ruta = os.path.join(CARPETA_CAPTURAS, time.strftime("error_%Y-%m-%d_%H-%M-%S.png"))
                context.pages[-1].screenshot(path=ruta, full_page=False)
                log(f"Se guardo una captura en {ruta}")
            except Exception:
                pass
            log("El navegador queda abierto por si quiere continuar a mano.")
        input("\nPresione Enter para cerrar el navegador...")
        navegador.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot detenido por el usuario.")
