import argparse
import NCBIQuery
import paperqa
from rmrkl import ChatZeroShotAgent
from langchain.chat_models import ChatOpenAI
from .utils import make_tools


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--question",
        type=str,
        nargs="+",
        help="Search by queuestion. keywords will be generated automatically.",
    )
    parser.add_argument(
        "--keywords", type=str, nargs="+", help="Search keywords. One or multiple."
    )
    parser.add_argument("--type", type=str, help="Publish type.")
    parser.add_argument(
        "--date",
        type=str,
        help="Date range of publishing. Must be 'YYYY/MM/DD:YYYY/MM/DD' format.",
    )  # YYYY/MM/DD:YYYY/MM/DD
    parser.add_argument(
        "--retmax",
        type=int,
        default=10000,
        help="Maximum numbers of pmids to return. At most 10,000.",
    )
    parser.add_argument(
        "-a",
        "--add",
        action="store_true",
        help="Append the new results to './paper_ids.txt' instead of overwriting it.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = get_arguments()
    if args.question is None and args.keywords is None:
        raise ValueError("Please enter question or keywords for searching.")
    if args.keywords:
        keywords = [" ".join(args.keywords)]
    elif args.question:
        docs = paperqa.Docs()
        question = " ".join(args.question)
        while question and question[-1] == '?':
            question = question[:-1]
        answer = paperqa.Answer(question=question)
        llm = ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo")
        agent = ChatZeroShotAgent.from_llm_and_tools(llm, make_tools(docs, answer))
        prompt = (
            f"Answer question: {question}. "
            f"Search for papers, gather evidence, and answer. "
            f"If you do not have enough evidence, "
            f"you can search for more papers (preferred) or gather more evidence. "
            f"You may rephrase or breaking-up the question in those steps. "
            f"Once you have five pieces of evidence, or you have tried for a while, "
            f"call the Propose Answer tool."
        )
        keywords = agent.plan(intermediate_steps=[], input=prompt).tool_input
        print("keywords generated based on your question: " + keywords)
        keywords = keywords.split(", ")

    for word in keywords:
        tags = []
        contents = []
        tags.append("tw")
        contents.append(word)
        if args.type is not None:
            tags.append("pt")
            contents.append(args.type)
        if args.date is not None:
            tags.append("dp")
            contents.append(args.date)
        output_file = "paper_ids.txt"
        result_ids = NCBIQuery.query_id("pubmed", tags, contents, retmax=args.retmax)

        if args.add:
            with open(output_file, "a", encoding="utf-8") as f:
                for id_ in result_ids:
                    f.write(id_ + "\n")
        else:
            with open(output_file, "w", encoding="utf-8") as f:
                for id_ in result_ids:
                    f.write(id_ + "\n")
        print(
            f'{len(result_ids)} papers have been found with keywords "{word}". '
            f'Result pmids appended to {output_file}.'
        )
