# 📚 Bot Scopus – Biblioteca SENA

Bot que abre el navegador, entra a la **Biblioteca del SENA**, va a **Bases de datos**, baja hasta **Scopus**, inicia sesión con tu número de documento, busca el tema que escribas, abre documentos y los "lee" (baja y sube la página con pausas, como una persona).

---

## ✅ Requisitos

| Requisito | Detalle |
|---|---|
| Sistema | Windows 10 u 11 |
| Python | 3.9 o superior |
| Navegador | Google Chrome o Microsoft Edge (si no hay ninguno, el bot descarga Chromium solo) |
| Cuenta | Usuario y contraseña de la biblioteca del SENA (número de documento) |

---

## 🛠️ Instalación

### 1. Instalar Python
1. Entra a <https://www.python.org/downloads/> y descarga la última versión.
2. Ejecuta el instalador y **marca la casilla `Add python.exe to PATH`** (muy importante).
3. Clic en **Install Now**.
4. Para comprobar, abre una ventana de comandos (`Win + R` → `cmd`) y escribe:
   ```
   python --version
   ```
   Debe mostrar algo como `Python 3.12.x`.

### 2. Descargar el proyecto
**Opción A – ZIP (más fácil):**
1. En esta página, clic en el botón verde **Code** → **Download ZIP**.
2. Descomprime el ZIP en el escritorio y renombra la carpeta a `SENA BIBLIOTECA` (opcional).

**Opción B – Git:**
```
git clone https://github.com/MarlonM001/BIBLIOTE.git "SENA BIBLIOTECA"
```

### 3. Primera ejecución
Doble clic en **`INICIAR_BOT.bat`**.
La primera vez instala automáticamente **Playwright** (la librería que controla el navegador). Solo tarda un par de minutos y no vuelve a pasar.

> Si prefieres instalarlo a mano:
> ```
> python -m pip install playwright
> ```

---

## ▶️ Uso

1. Doble clic en `INICIAR_BOT.bat`.
2. Responde lo que pide la ventana:

   | Pregunta | Qué escribir | Si das Enter |
   |---|---|---|
   | `Usuario:` | Tu número de documento | Obligatorio |
   | `Contrasena:` | Tu contraseña | Usa el mismo usuario |
   | `Que desea buscar:` | Tema, ej. `computadores` | `computadores` |
   | `Cuantos documentos abrir:` | Número de documentos | `1` |
   | `Minutos de lectura por documento:` | Minutos en cada uno | `3` |

3. El bot hace todo solo:
   1. Abre `https://biblioteca.sena.edu.co/`
   2. Clic en **Bases de datos**
   3. Baja hasta **Scopus** y entra
   4. Escribe usuario y contraseña en el login del SENA
   5. Busca el tema en Scopus
   6. Abre un documento de los primeros resultados y lo "lee" el tiempo indicado
4. Al final, presiona **Enter** en la ventana negra para cerrar el navegador.

---

## 📁 Estructura

```
SENA BIBLIOTECA/
├─ INICIAR_BOT.bat     ← lanzador (doble clic)
├─ LEEME.txt           ← instrucciones cortas
├─ README.md           ← este archivo
├─ codigo/
│   └─ bot_scopus.py   ← el programa
├─ capturas/           ← (se crea sola) imagen de la pantalla si algo falla
└─ registros/          ← (se crea sola) historial de cada ejecución, un archivo por día
```

---

## ❓ Problemas comunes

| Problema | Solución |
|---|---|
| `No se encontro Python` | Reinstala Python marcando **Add python.exe to PATH**. |
| Se queda en "Esperando el formulario…" | Revisa tu internet; el login del SENA a veces tarda. Vuelve a ejecutar. |
| `El login no paso` | Usuario o contraseña incorrectos. |
| `No encontre el campo de busqueda` | Scopus cambió su página. Mira la imagen en `capturas/` y reporta el problema. |
| Quieres detenerlo | Presiona `Ctrl + C` en la ventana negra. |

---

## 🔒 Seguridad

- Tu usuario y contraseña **no se guardan** en ningún archivo; solo se usan mientras el bot está abierto.
- Las carpetas `capturas/` y `registros/` están en `.gitignore` para que no se suban a GitHub.
