# 📅 Calendario 2027 - Mantenimiento Planeamiento Mina

Aplicación web colaborativa hecha con **Streamlit** y **GitHub** para marcar periodos o días en el Calendario 2027 (incluyendo semanas corporativas `3335`–`3387` y los 18 feriados considerados), con leyenda automática por persona/color y vista lista para imprimir.

## Características
- **Calendario 2027 completo** (12 meses, semanas `SEM.`, fines de semana y 18 feriados).
- **Leyenda dinámica**: cada persona elige un color y su nombre aparece automáticamente en la leyenda con el conteo de días.
- **Multiusuario y persistente**: si se configura `GITHUB_TOKEN` en Streamlit Secrets, cada cambio se guarda automáticamente en `data/asignaciones.json` dentro del repositorio de GitHub.
- **Listo para imprimir**: botón **Descargar Vista Imprimible (HTML)** optimizado para 1 página A4/Carta, o `Ctrl + P` directo en el navegador.

## Cómo ejecutar en tu PC
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Cómo publicar en GitHub + Streamlit Community Cloud
1. Sube esta carpeta a un repositorio en **GitHub**.
2. Entra a [share.streamlit.io](https://share.streamlit.io/), conecta tu cuenta de GitHub y selecciona tu repositorio con archivo principal `app.py`.
3. Para que los cambios de todas las personas se guarden permanentemente (y no se pierdan al reiniciarse la app):
   - En GitHub, crea un **Personal Access Token** (Fine-grained o Classic con permiso `Contents: Read and write` / `repo`).
   - En Streamlit Cloud, ve a **Settings → Secrets** y pega:
     ```toml
     GITHUB_TOKEN = "tu_token_aqui"
     GITHUB_REPO = "tu-usuario/tu-repositorio"
     GITHUB_BRANCH = "main"
     GITHUB_DATA_PATH = "data/asignaciones.json"
     ```
4. ¡Listo! Comparte el enlace de Streamlit con tu equipo.
