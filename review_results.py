import pandas as pd
import streamlit as st

from pathlib import Path


CSV_PATH = "./exp3_pairs.csv"


def load_csv(path: str) -> pd.DataFrame:
    """
    SUMMARY
    -------
    Carga un archivo CSV en un DataFrame de pandas.

    PARAMETERS
    ----------
    path : str
        Ruta al archivo CSV.

    RETURNS
    -------
    pd.DataFrame
        DataFrame con los datos del CSV.
    """
    df = pd.read_csv(path)
    if "result" not in df.columns:
        df["result"] = ""
    return df


def save_csv(path: str, df: pd.DataFrame) -> None:
    """
    SUMMARY
    -------
    Guarda un DataFrame de pandas en un archivo CSV.

    PARAMETERS
    ----------
    path : str
        Ruta al archivo CSV.
    df : pd.DataFrame
        DataFrame a guardar.
    """
    df.to_csv(path, index=False)


def get_filtered_indices(df: pd.DataFrame, only_unclassified: bool = True) -> list:
    """
    SUMMARY
    -------
    Obtiene los índices del DataFrame según el filtro especificado.

    PARAMETERS
    ----------
    df : pd.DataFrame
        DataFrame a filtrar.
    only_unclassified : bool, optional
        Si es True, solo se devuelven los índices de filas donde 'result' está vacío o NaN,
        por defecto True.

    RETURNS
    -------
    list
        Lista de índices filtrados.
    """
    if only_unclassified:
        mask = df["result"].isna() | (df["result"].astype(str).str.strip() == "")
        return list(df[mask].index)
    else:
        return list(df.index)


def go_to_next_unclassified(df: pd.DataFrame, only_unclassified: bool = True) -> None:
    """
    SUMMARY
    -------
    Mueve el índice actual al siguiente par dentro del filtro.

    PARAMETERS
    ----------
    df : pd.DataFrame
        DataFrame a filtrar.
    only_unclassified : bool, optional
        Si es True, solo se consideran filas donde 'result' está vacío o NaN,
        por defecto True.

    RETURNS
    -------
    None
        No retorna nada, solo actualiza el estado de la sesión.
    """
    filtered_indices = get_filtered_indices(df, only_unclassified)
    if not filtered_indices:
        st.session_state.current_idx = None
        return

    curr = st.session_state.current_idx
    if curr is None or curr not in filtered_indices:
        st.session_state.current_idx = filtered_indices[0]
        return

    pos = filtered_indices.index(curr)
    if pos + 1 < len(filtered_indices):
        st.session_state.current_idx = filtered_indices[pos + 1]
    else:
        st.session_state.current_idx = filtered_indices[-1]


def go_prev(df: pd.DataFrame, only_unclassified: bool = True) -> None:
    """
    SUMMARY
    -------
    Mueve el índice actual al par anterior dentro del filtro.

    PARAMETERS
    ----------
    df : pd.DataFrame
        DataFrame a filtrar.
    only_unclassified : bool, optional
        Si es True, solo se consideran filas donde 'result' está vacío o NaN,
        por defecto True.

    RETURNS
    -------
    None
        No retorna nada, solo actualiza el estado de la sesión.
    """
    filtered_indices = get_filtered_indices(df, only_unclassified)
    if not filtered_indices:
        st.session_state.current_idx = None
        return

    curr = st.session_state.current_idx
    if curr is None or curr not in filtered_indices:
        st.session_state.current_idx = filtered_indices[0]
        return

    pos = filtered_indices.index(curr)
    if pos - 1 >= 0:
        st.session_state.current_idx = filtered_indices[pos - 1]
    else:
        st.session_state.current_idx = filtered_indices[0]


def ensure_state(df: pd.DataFrame, only_unclassified: bool) -> None:
    """
    SUMMARY
    -------
    Asegura que el estado de la sesión tenga un índice actual válido.

    PARAMETERS
    ----------
    df : pd.DataFrame
        DataFrame a filtrar.
    only_unclassified : bool
        Si es True, solo se consideran filas donde 'result' está vacío o NaN.

    RETURNS
    -------
    None
        No retorna nada, solo actualiza el estado de la sesión.
    """
    if "current_idx" not in st.session_state:
        filtered_indices = get_filtered_indices(df, only_unclassified)
        st.session_state.current_idx = filtered_indices[0] if filtered_indices else None


def run_app() -> None:
    """
    SUMMARY
    -------
    Ejecuta la aplicación Streamlit para la revisión de resultados.
    """
    st.set_page_config(page_title="Revisión de resultados", layout="wide")

    st.title("Revisión de resultados")
    st.markdown("---")

    if "df" not in st.session_state:
        if not Path(CSV_PATH).exists():
            st.error(f"No se encontró el archivo CSV en: {CSV_PATH}")
            st.stop()
        st.session_state.df = load_csv(CSV_PATH)

    df = st.session_state.df

    st.sidebar.title("Configuración")
    st.sidebar.write(f"**CSV:** `{CSV_PATH}`")

    only_unclassified = st.sidebar.checkbox(
        "Mostrar solo pares sin clasificar",
        value=True,
        help="Si está activado, solo se muestran filas donde 'result' está vacío.",
    )

    if st.sidebar.button("Recargar CSV desde disco"):
        st.session_state.df = load_csv(CSV_PATH)
        df = st.session_state.df
        st.session_state.current_idx = None

    ensure_state(df, only_unclassified)

    filtered_indices = get_filtered_indices(df, only_unclassified)

    if not filtered_indices:
        st.warning("No hay pares de imágenes para mostrar con el filtro actual.")
        st.stop()

    if (
        st.session_state.current_idx is None
        or st.session_state.current_idx not in filtered_indices
    ):
        st.session_state.current_idx = filtered_indices[0]

    current_idx = st.session_state.current_idx
    row = df.loc[current_idx]

    pos = filtered_indices.index(current_idx)
    total = len(filtered_indices)

    st.write("### Acciones sobre decisiones")

    col_clear_one, col_clear_all = st.columns(2)

    with col_clear_one:
        if st.button("🧹 Limpiar decisión"):
            if current_idx is not None:
                df.at[current_idx, "result"] = ""
                st.session_state.df = df
                save_csv(CSV_PATH, df)
                st.success(f"Se limpió la decisión del índice {current_idx}")
                st.rerun()

    with col_clear_all:
        if st.button("🧼 Limpiar todos"):
            df["result"] = ""
            st.session_state.df = df
            save_csv(CSV_PATH, df)
            st.success("Se limpiaron todas las decisiones de la columna 'result'")
            st.rerun()

    st.markdown("---")
    st.write("### Navegación")

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ Atrás"):
            go_prev(df, only_unclassified)
            st.rerun()

    with col_next:
        if st.button("Adelante ➡️"):
            go_to_next_unclassified(df, only_unclassified)
            st.rerun()

    st.markdown("---")
    st.write("### Evaluar resultado")

    col_buttons = st.columns(5)
    labels = ["🟢 Muy bien", "✅ Bien", "⚪ Regular", "⚠️ Mal", "🔴 Muy mal"]

    clicked_label = None
    for c, label in zip(col_buttons, labels):
        with c:
            if st.button(label):
                clicked_label = label

    if clicked_label is not None:
        df.at[current_idx, "result"] = clicked_label
        st.session_state.df = df
        save_csv(CSV_PATH, df)
        go_to_next_unclassified(df, only_unclassified)
        st.success(f"Guardado resultado: '{clicked_label}' para índice {current_idx}")
        st.rerun()

    st.markdown("---")
    st.markdown(f"### Par {pos + 1} de {total} (índice global: {current_idx})")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Región de interés de la imagen antes")
        path1 = str(row["path_img1"])
        if Path(path1).exists():
            st.image(path1, width="stretch")
            info_path = Path(path1).parent / "info.txt"
            if info_path.exists():
                with open(info_path, "r") as f:
                    lines = f.readlines()
                info_dict = {}
                for line in lines:
                    if ":" in line:
                        k, v = line.strip().split(":", 1)
                        info_dict[k.strip()] = v.strip()
                mapping = {
                    "breast_density": "Densidad",
                    "mass_shape": "Forma",
                    "pathology": "Patología",
                    "assessment": "BI-RADS",
                    "view": "Vista",
                    "mass_margins": "Margen de la masa",
                }
                show_dict = {}
                subfolder = Path(path1).parent.name
                show_dict["ID"] = subfolder
                for k, v in mapping.items():
                    if k in info_dict:
                        show_dict[v] = info_dict[k]
                st.write(show_dict)
        else:
            st.error(f"No se encontró la imagen: {path1}")

    with col2:
        st.subheader("Región de interés de la imagen generada")
        path2 = str(row["path_img2"])
        if Path(path2).exists():
            st.image(path2, width="stretch")
        else:
            st.error(f"No se encontró la imagen: {path2}")

    st.markdown("---")
    st.write("## Clasificación de resultados")

    st.write(f"**Resultado actual en 'result':** {row.get('result', '')!r}")

    df_to_show = df.copy()
    df_to_show.index = df_to_show.index + 1

    df_to_show["path_img1"] = df_to_show["path_img1"].apply(lambda p: Path(p).name)
    df_to_show["path_img2"] = df_to_show["path_img2"].apply(lambda p: Path(p).name)

    st.dataframe(df_to_show)


def main():
    run_app()


if __name__ == "__main__":
    main()
