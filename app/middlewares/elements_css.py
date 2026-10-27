"""Ajustes de apresentação aplicados à interface Elements da documentação."""

from flask import Response, request


# ==============================================================================
# AJUSTE DA INTERFACE ELEMENTS
# ==============================================================================
def injetar_css_no_elements(response: Response) -> Response:
    """Ajusta a disposição das abas de resposta na página Elements.

    O script só é inserido na interface HTML do Elements; os demais tipos de
    resposta e endpoints permanecem inalterados.

    Args:
        response: Resposta Flask devolvida pela rota atual.

    Returns:
        A resposta recebida, com o script de layout quando aplicável.
    """
    if "/openapi/elements" in request.path and response.mimetype == "text/html":
        script_injecao: bytes = b"""
        <script>
          window.addEventListener("DOMContentLoaded", () => {
            const ajustarAbasDeResposta = () => {
              document
                .querySelectorAll(
                  ".sl-elements .HttpOperation .sl-link-heading[aria-label='Responses']"
                )
                .forEach((titulo) => {
                  const linha = titulo.parentElement;
                  const listaWrapper = titulo.nextElementSibling;
                  const tablist = listaWrapper?.querySelector("[role='tablist']");
                  if (!linha || !listaWrapper || !tablist) return;

                  const abas = Array.from(
                    tablist.querySelectorAll("[role='tab']")
                  );
                  const rotulos = abas.map((aba) =>
                    aba.textContent.trim().toLowerCase()
                  );
                  const listaDeStatus =
                    rotulos.length > 0 &&
                    rotulos.every((rotulo) =>
                      /^(default|\\d{3}(?:\\s.*)?)$/.test(rotulo)
                    );

                  if (!listaDeStatus) return;

                  linha.style.setProperty("display", "flex", "important");
                  linha.style.setProperty(
                    "flex-direction",
                    "column",
                    "important"
                  );
                  linha.style.setProperty(
                    "align-items",
                    "stretch",
                    "important"
                  );
                  linha.style.setProperty("gap", "8px", "important");

                  titulo.style.setProperty("order", "0", "important");
                  titulo.style.setProperty("width", "100%", "important");
                  titulo.style.setProperty("flex", "0 0 auto", "important");

                  listaWrapper.style.setProperty("order", "1", "important");
                  listaWrapper.style.setProperty("width", "100%", "important");
                  listaWrapper.style.setProperty("min-width", "0", "important");
                  listaWrapper.style.setProperty(
                    "align-self",
                    "stretch",
                    "important"
                  );
                  listaWrapper.style.setProperty(
                    "flex",
                    "0 0 auto",
                    "important"
                  );

                  tablist.style.setProperty("display", "flex", "important");
                  tablist.style.setProperty("flex-wrap", "wrap", "important");
                  tablist.style.setProperty("gap", "8px", "important");
                  tablist.style.setProperty("overflow", "visible", "important");
                  tablist.style.setProperty("white-space", "normal", "important");
                  tablist.style.setProperty("width", "100%", "important");
                });
            };

            ajustarAbasDeResposta();
            new MutationObserver(ajustarAbasDeResposta).observe(
              document.body,
              { childList: true, subtree: true }
            );
          });
        </script>
        </body>
        """
        response.data = response.data.replace(b"</body>", script_injecao)

    return response


__all__ = ["injetar_css_no_elements"]
