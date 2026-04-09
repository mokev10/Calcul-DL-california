import streamlit as st

st.title("Health Check pdf417gen")

try:
    import pdf417gen
    from pdf417gen import encode, render_svg
    st.success("Import pdf417gen OK")
    st.write("pdf417gen module path:", pdf417gen.__file__)
    try:
        codes = encode(b"TEST", columns=3, security_level=2, force_binary=False)
        st.write("encode() returned type:", type(codes).__name__)
    except Exception as e:
        st.warning("encode() raised an exception: " + str(e))
    st.write("render_svg available:", callable(render_svg))
except Exception as exc:
    st.error("Import pdf417gen failed: " + str(exc))
    st.info("Vérifiez que le dossier pdf417gen/ est à la racine et contient __init__.py")
