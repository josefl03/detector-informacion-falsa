from typing import *
import openai
import os
from loguru import logger
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from abc import ABC, abstractmethod
import sys
from google import genai
from google.genai import types
import base64

sys.path.append("libreria/")
import fake_news_detector.utils as utils
import fake_news_detector.debug as debug

# ========= Default models

# OpenRouter
OPENROUTER_LLAMA3_VISION = "meta-llama/llama-3.2-11b-vision-instruct"
OPENROUTER_LLAMA4_SCOUT = "meta-llama/llama-4-scout"

OPENROUTER_GEMMA3_12B = "google/gemma-3-12b-it"
OPENROUTER_GEMMA3_27B = "google/gemma-3-27b-it"

OPENROUTER_GPT41_MINI = "openai/gpt-4.1-mini"
OPENROUTER_GPT41 = "openai/gpt-4.1"

# Ollama
OLLAMA_GEMMA3_27B = "gemma3:27b"

# OpenAI
OPENAI_GPT41 = "gpt-4.1"

# ========= Configs

MAX_TOKENS = 32 * 1024  # 32k tokens
OLLAMA_NUM_CTX = 8 * 1024  # Ollama context size

# =========
    
class LLM:
    input_usage: int = 0
    output_usage: int = 0
    
    def __init__(self, model: str, endpoint: str = None, api_key: str = None, extra_body: Optional[Dict[str, Any]] = None):
        self.model = model
        self.api_key = api_key
        self.endpoint = endpoint
        
        secret_api_key = api_key
        if api_key:
            secret_api_key = secret_api_key[:8] + "..."
        
        logger.debug(f"Using model {self.model} with API key {secret_api_key} at endpoint {self.endpoint}")

        self.client = openai.Client(
            api_key=self.api_key or "dummy",
            base_url=self.endpoint,
        )
        
        self.extra_body = extra_body

    def call(self,
             messages: "ChatBuilder",
             temperature: float = None,
             structure: Any = None
             ) -> Any:
        """
        Call the LLM with the given parameters.

        Args:
            sys_prompt (str): System prompt to set the behavior of the model.
            prompt (str): User prompt to generate a response.
            temperature (float): Sampling temperature for the model.
            structure (Any): Structure of the response.
        """
        # Choose the correct function
        if structure:
            func = self.client.beta.chat.completions.parse
            logger.debug(f"Calling ChatCompletionsParse with model {self.model} at {self.endpoint}")
        else:
            func = self.client.chat.completions.create
            logger.debug(f"Calling ChatCompletions with model {self.model} at {self.endpoint}")
            
        assert self.model, "Model not set"
        assert self.api_key, "API key not set"
        assert messages, "Messages not set"
        assert isinstance(messages, ChatBuilder), "Messages must be an instance of ChatBuilder"
        assert isinstance(messages.build(), list), "Messages must be a list"
        assert len(messages.build()) > 0, "Messages must not be empty"
        assert isinstance(temperature, (float, int, type(None))), "Temperature must be a float, int or None"
        assert isinstance(structure, (type, type(None))), "Structure must be a type or None"
        assert isinstance(self.model, str), "Model must be a string"
        assert isinstance(self.api_key, str), "API key must be a string"
        assert isinstance(self.endpoint, (str, type(None))), "Endpoint must be a string or None"
        
        logger.trace(f"Messages: {messages.build()}")
        
        resp = self._call(
            func=func,
            messages=messages,
            temperature=temperature,
            structure=structure
        )
        
        input_tokens = resp.usage.prompt_tokens
        output_tokens = resp.usage.completion_tokens
        
        self.input_usage += input_tokens
        self.output_usage += output_tokens
        
        logger.debug(f"Recieved response. Input tokens: {input_tokens}, Output tokens: {output_tokens}")
        
        if structure:
            result = resp.choices[0].message.parsed
            logger.trace(utils.short(str(result)))
        else:
            result = resp.choices[0].message.content
            logger.trace(utils.short(result))
        
        return result
    
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=30))
    def _call(
        self,
        func: Callable,
        messages: "ChatBuilder",
        temperature: float = None,
        structure: Any = None
    ):
        try:
            return func(
                model=self.model,
                messages=messages.build(),
                temperature=temperature,
                response_format=structure,
                extra_body=self.extra_body,
                max_tokens=MAX_TOKENS,
            )
        except (openai.RateLimitError, openai.APIStatusError) as e:
            logger.error(f"Rate limit error: {e}")
            utils.wait_input(f"Analysis paused to wait for funds refill dor: {self.endpoint}")
            raise

    def models(self):
        """
        Get all available models.
        """
        return self.client.models.list()
    
    def get_usage(self) -> Tuple[int, int]:
        """
        Get the usage of the LLM.
        
        Returns:
            Tuple[int, int]: A tuple containing the input and output token usage.
        """
        return self.input_usage, self.output_usage
    
    def get_model(self) -> str:
        """
        Get the model name.
        
        Returns:
            str: The model name.
        """
        return self.model
    
    def get_endpoint(self) -> str:
        """
        Get the endpoint URL.
        
        Returns:
            str: The endpoint URL.
        """
        return self.endpoint
    

    
class GoogleLLM:
    input_usage: int = 0
    output_usage: int = 0
    
    def __init__(self, model: str, endpoint: str = None, api_key: str = None, extra_body: Optional[Dict[str, Any]] = None):
        self.model = model
        self.api_key = api_key
        self.endpoint = endpoint
        
        secret_api_key = api_key
        if api_key:
            secret_api_key = secret_api_key[:8] + "..."
        
        logger.debug(f"Using model {self.model} with API key {secret_api_key} at endpoint {self.endpoint}")

        self.client = genai.Client(
            api_key=self.api_key or "dummy",
        )
        
        self.extra_body = extra_body

    def call(self,
             messages: "ChatBuilder",
             temperature: float = None,
             structure: Any = None
             ) -> Any:
        """
        Call the LLM with the given parameters.

        Args:
            sys_prompt (str): System prompt to set the behavior of the model.
            prompt (str): User prompt to generate a response.
            temperature (float): Sampling temperature for the model.
            structure (Any): Structure of the response.
        """
        # Choose the correct function
        logger.debug(f"Calling GenerateContent with model {self.model} at {self.endpoint}")
            
        assert self.model, "Model not set"
        assert self.api_key, "API key not set"
        assert messages, "Messages not set"
        assert isinstance(messages, ChatBuilder), "Messages must be an instance of ChatBuilder"
        assert isinstance(messages.build(), list), "Messages must be a list"
        assert len(messages.build()) > 0, "Messages must not be empty"
        assert isinstance(temperature, (float, int, type(None))), "Temperature must be a float, int or None"
        assert isinstance(structure, (type, type(None))), "Structure must be a type or None"
        assert isinstance(self.model, str), "Model must be a string"
        assert isinstance(self.api_key, str), "API key must be a string"
        assert isinstance(self.endpoint, (str, type(None))), "Endpoint must be a string or None"
        
        logger.trace(f"Messages: {messages.build()}")
        
        resp = self._call(
            messages=messages,
            temperature=temperature,
            structure=structure
        )
        
        input_tokens = resp.usage_metadata.prompt_token_count or 0
        output_tokens = resp.usage_metadata.candidates_token_count or 0
        
        self.input_usage += input_tokens
        self.output_usage += output_tokens
        
        logger.debug(f"Recieved response. Input tokens: {input_tokens}, Output tokens: {output_tokens}")
        
        if structure:
            result = resp.parsed
            logger.trace(utils.short(str(result)))
        else:
            result = resp.text
            logger.trace(utils.short(result))
        
        return result
    
    #@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=30))
    def _call(
        self,
        messages: "ChatBuilder",
        temperature: float = None,
        structure: Any = None,
        func: Callable=None,
    ):
        structure_mime = None
        if structure:
            structure_mime = "application/json"  
        
        # Convert contents
        system = None
        contents = []
        for msg in messages.build():
            if msg["role"] == "system":
                system = msg["content"]
            
            # TODO: assistant
            
            elif msg["role"] == "user":
                content = msg["content"]
                if isinstance(content, str):
                    # User prompts
                    contents.append(
                        content
                    )
                elif isinstance(content, list):
                    for content in msg["content"]:
                        # User prompts
                        if content["type"] == "text":
                            contents.append(content["text"])
                            
                        # Images
                        elif content["type"] == "image_url":
                            # Convert base 64 image to bytes
                            img_b64 = content["image_url"]["url"]
                            
                            mime = img_b64.split(";")[0].split(":")[1]
                            
                            # Remove the prefix
                            if img_b64.startswith("data:"):
                                img_b64 = img_b64.split(",")[1]
                            
                            img_b = base64.b64decode(img_b64)
                            
                            logger.debug(f"Converted image with mime type {mime} to bytes: {img_b[:10]}...")

                            contents.append(
                                types.Part.from_bytes(
                                    data=img_b,
                                    mime_type=mime,
                                )
                            )
                            
                        # Documents
                        elif content["type"] == "file":
                            # Convert base 64 file to bytes
                            file_b64 = content["file"]["file_data"]
                            
                            mime = "application/pdf"
                            
                            # Remove the prefix
                            if file_b64.startswith("data:"):
                                file_b64 = file_b64.split(",")[1]

                            file_b = base64.b64decode(file_b64)

                            logger.debug(f"Converted file with mime type {mime} to bytes: {file_b[:10]}...")

                            contents.append(
                                types.Part.from_bytes(
                                    data=file_b,
                                    mime_type=mime,
                                )
                            )
                            
        try:
            resp = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    response_mime_type=structure_mime,
                    response_schema=structure,
                    temperature=temperature,
                    system_instruction=system,
                    max_output_tokens=MAX_TOKENS,
                )
            )
            
            return resp
        except Exception as e:
            logger.error(f"Error: {e}")
            utils.wait_input(f"Analysis paused. Endpoint: {self.endpoint}")
            raise

    def models(self):
        """
        Get all available models.
        """
        return self.client.models.list()
    
    def get_usage(self) -> Tuple[int, int]:
        """
        Get the usage of the LLM.
        
        Returns:
            Tuple[int, int]: A tuple containing the input and output token usage.
        """
        return self.input_usage, self.output_usage
    
    def get_model(self) -> str:
        """
        Get the model name.
        
        Returns:
            str: The model name.
        """
        return self.model
    
    def get_endpoint(self) -> str:
        """
        Get the endpoint URL.
        
        Returns:
            str: The endpoint URL.
        """
        return self.endpoint
        
class OpenAI(LLM):
    def __init__(self, model: str):
        super().__init__(
            model=model,
            api_key=os.getenv("OPENAI_API_KEY"),
            endpoint=os.getenv("OPENAI_BASE_URL")
        )

class OpenRouter(LLM):
    def __init__(self, model: str):
        super().__init__(
            model=model,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            endpoint=os.getenv("OPENROUTER_BASE_URL"),
            extra_body={
                # OpenRouter-specific params
                "data_collection": "deny",
                "allow_fallbacks": True,
                "require_parameters": True,
            }
        )
        
class Ollama(LLM):
    def __init__(self, model: str):
        super().__init__(
            model=model,
            api_key=os.getenv("OPENAI_API_KEY"),
            endpoint=os.getenv("OLLAMA_BASE_URL"),
            extra_body={
                # Ollama-specific params
                "options":{
                    "num_ctx": OLLAMA_NUM_CTX,
                }
            }
        )
        
# Embeddings
class Embeddings(ABC):
    @abstractmethod
    def __init__(self):
        pass
    
    @abstractmethod
    def get_embeddings(self, text: str) -> list[float]:
        """
        Embed the given text using the embedding model.
        
        Args:
            text (Union[str, list[str]]): The text to embed. Can be a single string or a list of strings.
            
        Returns:
            list: A list of embeddings for the input text.
        """
        pass
    
class OllamaEmbeddings(Embeddings):
    def __init__(self, model:str, endpoint: str = None, api_key: str = None):
        
        llm = Ollama(model=model)
        
        self.client = llm.client
        self.endpoint = llm.endpoint
        self.model = model
        
    def get_embeddings(self, text: str) -> list[float]:
        logger.debug(f"Generating embeddings with model {self.model} at {self.endpoint}")
        
        resp = self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        
        return resp.data[0].embedding

# Define the generic services       
GENERIC_SERVICES = [
    "openai",
    "openrouter",
    "ollama",
    "ollama-embeddings",
    "custom",
    "custom-google",
] 

class GenericLLM():
    @classmethod
    def choose(cls, model: str, service: str):
        assert service in GENERIC_SERVICES, f"Service must be one of {GENERIC_SERVICES}"
        
        if service == "openai":
            return OpenAI(model=model)
        elif service == "openrouter":
            return OpenRouter(model=model)
        elif service == "ollama":
            return Ollama(model=model)
        elif service == "ollama-embeddings":
            return OllamaEmbeddings(model=model)
        elif service == "custom":
            return LLM(model=model, endpoint=os.getenv("CUSTOM_BASE_URL"), api_key=os.getenv("CUSTOM_API_KEY"))
        elif service == "custom-google":
            return GoogleLLM(model=model, endpoint=os.getenv("CUSTOM_BASE_URL"), api_key=os.getenv("CUSTOM_API_KEY"))

API_FORMATS = [
    "default",
    ]

class ChatBuilder:
    messages: List

    def __init__(self):
        self.messages = []

    def system(self, prompt: str):
        assert prompt, "System prompt must not be empty"
        
        self.messages.append({"role": "system", "content": prompt})
        return self
    
    def assistant(self, prompt: str):
        assert prompt, "Assistant prompt must not be empty"
        
        self.messages.append({"role": "assistant", "content": prompt})
        return self

    def user(self, prompt: str = None, image_uri = None, pdf_uri = None, pdf_name = None):
        content = prompt
        
        attachment = image_uri or pdf_uri
        if attachment:
            content = []
            
            # Include an image
            if image_uri is not None:
                assert image_uri != "", "Image URI must not be empty"
                
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_uri
                    }
                })
            # Include a pdf
            if pdf_uri or pdf_name:
                assert pdf_uri, "PDF URI must be provided if PDF name is given"
                assert pdf_name, "PDF name must be provided if PDF URI is given"
                
                content.append({
                    "type": "file",
                    "file": {
                        "file_data": pdf_uri,
                        "filename": pdf_name or "file.pdf",
                    }
                })
                
            content.append({
                "type": "text",
                "text": prompt or " "
            })
        self.messages.append({"role": "user", "content": content})
        return self
    
    def build(self):
        return self.messages

# Test
if __name__ == "__main__":
    debug.setup(skip_checks=True)
    
    # Initialize OPENAI client
    # openai_client = LLM(
    #     model="gpt-4o",
    #     api_key=os.getenv("OPENAI_API_KEY")
    # )
    
    openai_client = OpenRouter(OPENROUTER_LLAMA3_VISION)

    # List models
    def list_models():
        models = openai_client.models()
        logger.info("Available models:")
        for model in models.data:
            logger.info(f"- {model.id}")
    #list_models()

    # test openai
    def test_prompt():
        msgs = ChatBuilder()
        msgs.system("Say everything in uppercase")
        msgs.user("Say hello")

        response = openai_client.call(
            messages=msgs,
        )
        assert "HELLO" in response
        logger.success("Prompt test passed")
    #test_prompt()

    def test_image():
        msgs = ChatBuilder()
        msgs.system("Say everything in uppercase")
        msgs.image_prompt("What's in this image?", utils.image_to_b64("../../../dummy/capybara.jpg"))

        response = openai_client.call(
            messages=msgs,
        )
        assert "capybara" in response.lower()
        logger.success("Image test passed")
    #test_image()
    
    def test_structure():
        class TestClass(BaseModel):
            name: str
            surname: str
            age: int
        
        msgs = ChatBuilder()
        msgs.system("Say everything in uppercase")
        msgs.user("What's in this image?")

        response = openai_client.call(
            messages=msgs,
            structure=TestClass
        )
        assert isinstance(response, TestClass)
        logger.success("Structured test passed")
    #test_structure()
    
    def test_pdf():
        pdf = utils.load("dummy/test_b64.txt")
        
        msgs = ChatBuilder()
        msgs.user("What's in this pdf? Include all existing details", pdf_name= "test.pdf", pdf_uri=pdf)

        response = openai_client.call(
            messages=msgs,
        )
        logger.debug(response)
    #test_pdf()
    
    # def test_html():
    #     html = utils.load("dummy/test_cleaned.html")
        
    #     msgs = ChatBuilder()
    #     msgs.user("What's in this html? Include all existing details", pdf_name= "weboage.html", pdf_uri=html)

    #     response = openai_client.call(
    #         messages=msgs,
    #     )
    #     logger.debug(response)
    # test_html()
    
    SERVICES = [
        (os.getenv("EMBEDDINGS_SERVICE"), os.getenv("EMBEDDINGS_MODEL")),
        (os.getenv("PDF_SERVICE"), os.getenv("PDF_MODEL")),
        (os.getenv("TEXT_SERVICE"), os.getenv("TEXT_MODEL")),
    ]
    
    def test_services():
        for service, model in SERVICES:
            if not service or not model:
                logger.warning(f"Service {service} or model {model} is not defined. Skipping test.")
                continue
            
            logger.info(f"Testing service {service} with model {model}")
            llm = GenericLLM.choose(model=model, service=service)
            
            if not service.endswith("-embeddings"):
                msgs = ChatBuilder()
                msgs.system("Say everything in uppercase")
                msgs.user("Say hello")

                response = llm.call(
                    messages=msgs,
                )
                logger.debug(f"Response from {service}: {response[:5]}")
                
                assert "HELLO" in response
            else:
                # For embeddings, we just check if we can get embeddings
                text = "This is a test text for embeddings."
                embeddings = llm.get_embeddings(text)
                logger.debug(f"Embeddings for '{text}': {embeddings[:3]}...")  # Print first 10 embeddings for brevity
                assert isinstance(embeddings, list) and len(embeddings) > 0, "Embeddings should be a non-empty list"
                
            logger.success(f"Service {service} test passed")
            
    #test_services()
    
    def test_proxied_llm():
        # Test the proxied LLM
        llm = GenericLLM.choose(
            model=os.getenv("PDF_MODEL"),
            service="custom-google"
        )
        
        msgs = ChatBuilder()
        msgs.system("Say everything in uppercase")
        msgs.user("Say hello")

        response = llm.call(
            messages=msgs,
        )
        
        logger.debug(f"Response from proxied LLM: {response}")
        assert "HELLO" in response
        logger.success("Proxied LLM test passed")
    #test_proxied_llm()
    
    def test_google_llm():
        google_llm = GenericLLM.choose(
            model=os.getenv("PDF_MODEL"),
            service="custom-google"
        )
        
        msgs = ChatBuilder()
        msgs.system("Say everything in uppercase")
        msgs.user("Say hello and add some extra data to make it longer")

        response = google_llm.call(
            messages=msgs,
        )
        
        logger.debug(f"Response from Google LLM: {response}")
        assert "HELLO" in response
        logger.success("Google LLM test passed")
    #test_google_llm()
    
    
    def test_google_llm_with_image():
        google_llm = GenericLLM.choose(
            model=os.getenv("PDF_MODEL"),
            service="custom-google"
        )
        
        msgs = ChatBuilder()
        msgs.system("Describe the image")
        # Use a sample image path; replace with your actual image if needed
        image_b64 = utils.image_to_b64("libreria/dummy/capybara.jpeg")
        msgs.user("What animal is in this image?", image_uri=image_b64)

        response = google_llm.call(
            messages=msgs,
        )
        
        logger.debug(f"Response from Google LLM (image): {response}")
        assert any(word in response.lower() for word in ["capybara", "animal", "rodent"]), "Expected animal description in response"
        logger.success("Google LLM image test passed")
    #test_google_llm_with_image()
    
    def test_google_llm_structured():
        from pydantic import BaseModel
        class AnimalInfo(BaseModel):
            name: str
            type: str
            habitat: str

        google_llm = GenericLLM.choose(
            model=os.getenv("PDF_MODEL"),
            service="custom-google"
        )
        
        msgs = ChatBuilder()
        msgs.system("Return the following fields in JSON: name, type, habitat for a capybara.")
        msgs.user("Give me the animal info for a capybara.")

        response = google_llm.call(
            messages=msgs,
            structure=AnimalInfo
        )
        
        logger.debug(f"Structured response from Google LLM: {response}")
        assert isinstance(response, AnimalInfo)
        assert response.name.lower() == "capybara"
        logger.success("Google LLM structured output test passed")
    #test_google_llm_structured()
    
    def test_google_llm_structured_pdf():
        from pydantic import BaseModel
        class PDFInfo(BaseModel):
            title: str
            author: str
            num_pages: int

        google_llm = GenericLLM.choose(
            model=os.getenv("PDF_MODEL"),
            service="custom-google"
        )
        
        pdf_b64 = utils.load_b64("libreria/dummy/elpais.pdf")
        msgs = ChatBuilder()
        msgs.system("Extract the following fields from the PDF: title, author, num_pages. Respond in JSON.")
        msgs.user("Extract info from this PDF.", pdf_name="test.pdf", pdf_uri=pdf_b64)

        response = google_llm.call(
            messages=msgs,
            structure=PDFInfo
        )
        
        logger.debug(f"Structured PDF response from Google LLM: {response}")
        assert isinstance(response, PDFInfo)
        assert response.title, "Title should not be empty"
        assert response.num_pages > 0, "Number of pages should be positive"
        logger.success("Google LLM structured PDF output test passed")
    #test_google_llm_structured_pdf()

