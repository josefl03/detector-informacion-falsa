from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class Prompt():
    system: Optional[str] = None
    user: Optional[str | list[str]] = None
    temperature: float = None

ARTICLE_CLASSIFICATION = Prompt(
    user = "Classify this PDF dump of a webpage, to see if it's an article from a newspaper or not."
)

PDF_HTML_TO_STRUCTURED = Prompt(
    system = """\
I will give you a markdown and a PDF file. Your goal is to parse the contents of the article to the provided JSON format. Focus on the content inside the article, and discard anything else.
Include any image present inside the article, as well as a brief description of it inside the alt text field.
Don't explain anything, only parse the article and it's contents. Use the same language as the article.
The Markdown format must be the following:
# title
## subtitle
### section if any
**date**

article content
[Alt Text](URL)
![Image Alt Text](Image URL)
> cites or tweets""",
    #user="<place your markdown here>"
)

QUESTION_GENERATION = Prompt(
    system = "Transforma el siguiente resumen de una noticia en una pregunta para un motor de búsqueda. La pregunta debe ser breve y detallada. En texto plano. Escribe solo la pregunta. No añadas nada más.",
)

COMPARISON = Prompt(
    system = 'I will give you two texts, and you have to compare them and indicate "verified" if both say similar information, "unverified" if they don\'t match, or "unrelated" if both text have no relation.',
    user = "--- Text 1\n{text1}\n\n--- Text 2\n{text2}",
    temperature=0.5
)

ARTICLE_SUMMARIZATION = Prompt(
    system = "Resume la noticia a su mínima expresión, manteniendo absolutamente todos los detalles mencionados. En un solo párrafo corto. Incluye negritas para hacer énfasis.",
)

WEBPAGE_SUMMARIZATION = Prompt(
    system = "Esto es un artículo convertido de HTML a Markdown. Tu objetivo es resumir únicamente el contenido del artículo, descartando todo lo demás. Incluye todos los detalles del artículo. En un párrafo, en texto plano.",
)

CONCLUSION_GENERATION = Prompt(
    #system = """Analiza las fuentes de esta noticia y haz un breve resumen con las partes que coinciden con la noticia original y con las que no. Cita las fuentes utilizando [] con el número correspondiente. Sé muy muy breve. En un párrafo. Omite información no necesaria. Resalta las palabras más importantes con negrita en formato Markdown. Refiérete a los artículos como "los medios" o "las fuentes". No repitas información. No hagas resúmenes ni conclusiones.""",
    system= """Analiza las fuentes y compáralas con el contenido del artículo original. Escribe muy brevemente en qué partes coinciden y en cuáles difieren. Cita las fuentes únicamente con [] y el número correspondiente. No uses coletillas ni escribas conclusiones o resúmenes al final. Un solo párrafo. Pon en negrita las palabras más importantes.""",
    # user = None # Built at runtime
    user = [
        """--- Noticia Original: {article}\n\n--- Fuentes Consultadas:\n{sources}""",
        "Resumen"
    ],
    temperature=0
)

GRAMMAR_CLASSIFICATION = Prompt(
    system = """Comprueba si el texto dentro de este archivo HTML contiene alguna falta de ortografía o algún error de gramática. No incluyas errores por tildes. Indica brévemente dónde (si las hubiera). No expliques nada.""",
    temperature=0
)