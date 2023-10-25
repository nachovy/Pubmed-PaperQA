import copy
import langchain.prompts as prompts
from datetime import datetime
from typing import Any, Dict, List, Optional
from langchain.agents import AgentType, initialize_agent
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool
from rmrkl import ChatZeroShotAgent, RetryAgentExecutor
from paperqa.docs import Answer, Docs
from langchain.callbacks.manager import AsyncCallbackManagerForChainRun
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import LLMResult, SystemMessage

def _get_datetime():
    now = datetime.now()
    return now.strftime("%m/%d/%Y")


citation_prompt = prompts.PromptTemplate(
    input_variables=["text"],
    template="Provide a citation for the following text in MLA Format. You must answer. Today's date is {date}\n"
    "{text}\n\n"
    "Citation:",
    partial_variables={"date": _get_datetime},
)


class FallbackLLMChain(LLMChain):
    """Chain that falls back to synchronous generation if the async generation fails."""

    async def agenerate(
        self,
        input_list: List[Dict[str, Any]],
        run_manager: Optional[AsyncCallbackManagerForChainRun] = None,
    ) -> LLMResult:
        """Generate LLM result from inputs."""
        try:
            return await super().agenerate(input_list, run_manager=run_manager)
        except NotImplementedError as e:
            return self.generate(input_list, run_manager=run_manager)


def make_chain(prompt, llm):
    if type(llm) == ChatOpenAI:
        system_message_prompt = SystemMessage(
            content="You are a scholarly researcher that answers in an unbiased, concise, scholarly tone. "
            "You sometimes refuse to answer if there is insufficient information. "
            "If there are potentially ambiguous terms or acronyms, first define them. ",
        )
        human_message_prompt = HumanMessagePromptTemplate(prompt=prompt)
        prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )
    return FallbackLLMChain(prompt=prompt, llm=llm)


def status(answer: Answer, docs: Docs):
    return f" Status: Current Papers: {len(docs.doc_previews())} Current Evidence: {len(answer.contexts)} Current Cost: ${answer.cost:.2f}"

class Search(BaseTool):
    name = "Paper Search"
    description = (
        "Generate some keywords of papers that to be searched in order to answer this question, separated by commas."
    )
    docs: Docs = None
    answer: Answer = None

    def __init__(self, docs, answer):
        # call the parent class constructor
        super(Search, self).__init__()

        self.docs = docs
        self.answer = answer

    def _run(self, query: str) -> str:
        raise NotImplementedError()

    def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError()


def make_tools(docs, answer):
    tools = []

    tools.append(Search(docs, answer))
    return tools
