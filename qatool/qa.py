import argparse
import os
import pickle
import string
from tqdm import tqdm
from paperqa import Docs
from paperqa.types import Doc
from paperqa.readers import read_doc
from paperqa.utils import md5sum


def format_filename(s):
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    filename = "".join(c for c in s if c in valid_chars)
    filename = filename.replace(" ", "_")
    if not any(c.isdigit() for c in filename) and not any(
        c.isalpha() for c in filename
    ):
        raise ValueError("Library name invalid!")
    return filename


def get_arguments():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-l",
        "--load",
        nargs="?",
        const="./saved_papers",
        type=str,
        help="Load papers from given directory or file. Load from './saved_papers' by default.",
    )
    parser.add_argument(
        "--lib_name",
        type=str,
        help="Name of the paper library: an existing name or a new name. "
        "The library will be loaded or saved as pkl file in './saved_libs' directory.",
    )
    group.add_argument(
        "-r", "--run", action="store_true", help="Run command line QA tool."
    )
    group.add_argument("-w", "--web", action="store_true", help="Run webpage QA tool.")
    parser.add_argument(
        "--port",
        type=int,
        default=80,
        help="Which port should webpage QA tool use. Default value 80.",
    )
    parser.add_argument(
        "--embeddings",
        type=str,
        default="all-mpnet-base-v2",
        help="Specify embedding model.",
    )
    return parser.parse_args()


def get_embedding_model(embeddings):
    if embeddings in ["hkunlp/instructor-large", "hkunlp/instructor-xl"]:
        from langchain.embeddings import HuggingFaceInstructEmbeddings

        model_kwargs = {"device": "cpu"}
        encode_kwargs = {"normalize_embeddings": True}
        return HuggingFaceInstructEmbeddings(
            model_name=embeddings,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )
    from langchain.embeddings.huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=embeddings)


def get_chunked_texts(doc_dir):
    texts_list = []
    if os.path.isdir(doc_dir):
        file_names = os.listdir(doc_dir)
        file_list = [
            os.path.join(doc_dir, f)
            for f in file_names
            if os.path.isfile(os.path.join(doc_dir, f))
        ]
    else:
        file_list = [doc_dir]
    for f in tqdm(file_list):
        fake_doc = Doc(docname="", citation="", dockey=md5sum(f))
        try:
            texts = read_doc(f, fake_doc, chunk_chars=3000)
            if len(texts) == 0:
                continue
            for single_texts in texts:
                texts_list.append(single_texts.text)
        except Exception as exception:
            print(exception)
            continue
    return texts_list


def get_embeddings(doc_dir, embeddings_name="all-mpnet-base-v2"):
    if embeddings_name is None or embeddings_name == "":
        return get_chunked_texts(doc_dir), []
    if os.path.isdir(doc_dir):
        file_names = os.listdir(doc_dir)
        file_list = [
            os.path.join(doc_dir, f)
            for f in file_names
            if os.path.isfile(os.path.join(doc_dir, f))
        ]
    else:
        file_list = [doc_dir]
    embeddings = get_embedding_model(embeddings_name)
    texts_list = []
    embeddings_list = []
    for f in tqdm(file_list):
        if not os.path.isfile(f):
            continue
        fake_doc = Doc(docname="", citation="", dockey=md5sum(f))
        texts = read_doc(f, fake_doc, chunk_chars=3000)
        try:
            if len(texts) == 0:
                continue
            text_embeddings = embeddings.embed_documents([t.text for t in texts])
            for single_texts, single_embeddings in zip(texts, text_embeddings):
                texts_list.append(single_texts.text)
                embeddings_list.append(single_embeddings)
        except Exception as e:
            print(e)
            continue
    return texts_list, embeddings_list


def get_chunked_texts_with_source(doc_dir):
    texts_list = []
    if os.path.isdir(doc_dir):
        file_names = os.listdir(doc_dir)
        file_list = [
            os.path.join(doc_dir, f)
            for f in file_names
            if os.path.isfile(os.path.join(doc_dir, f))
        ]
    else:
        file_list = [doc_dir]
    for f in tqdm(file_list):
        if not os.path.isfile(f):
            continue
        fake_doc = Doc(docname="", citation="", dockey=md5sum(f))
        try:
            texts = read_doc(f, fake_doc, chunk_chars=3000)
            if len(texts) == 0:
                continue
            for single_texts in texts:
                texts_list.append((f, single_texts.text))
        except Exception as exception:
            print(exception)
            continue
    return texts_list


def get_embeddings_with_source(doc_dir, embeddings_name="all-mpnet-base-v2"):
    if embeddings_name is None or embeddings_name == "":
        return get_chunked_texts_with_source(doc_dir), []
    if os.path.isdir(doc_dir):
        file_names = os.listdir(doc_dir)
        file_list = [
            os.path.join(doc_dir, f)
            for f in file_names
            if os.path.isfile(os.path.join(doc_dir, f))
        ]
    else:
        file_list = [doc_dir]
    embeddings = get_embedding_model(embeddings_name)
    texts_list = []
    embeddings_list = []
    for f in tqdm(file_list):
        if not os.path.isfile(f):
            continue
        fake_doc = Doc(docname="", citation="", dockey=md5sum(f))
        try:
            texts = read_doc(f, fake_doc, chunk_chars=3000)
            if len(texts) == 0:
                continue
            text_embeddings = embeddings.embed_documents([t.text for t in texts])
            for single_texts, single_embeddings in zip(texts, text_embeddings):
                texts_list.append((f, single_texts.text))
                embeddings_list.append((f, single_embeddings))
        except Exception as exception:
            print(exception)
            continue
    return texts_list, embeddings_list


def load_papers(doc_dir, lib_name, embeddings):
    llm = "gpt-3.5-turbo"
    embeddings = get_embedding_model(embeddings)
    lib_dir = "./saved_libs/" + lib_name + ".pkl"
    if os.path.exists(lib_dir):
        docs = pickle.load(open(lib_dir, "rb"))
    else:
        docs = Docs(llm=llm, embeddings=embeddings)
    if os.path.isdir(doc_dir):
        file_names = os.listdir(doc_dir)
        file_list = [
            os.path.join(doc_dir, f)
            for f in file_names
            if os.path.isfile(os.path.join(doc_dir, f))
        ]
    else:
        file_list = [doc_dir]
    for f in tqdm(file_list):
        if not os.path.isfile(f):
            continue
        if f in docs.docs:
            continue
        if os.stat(f).st_size == 0:
            continue
        try:
            if f.endswith('.txt'): # do not generate citations for txt chunks
                docs.add(f, chunk_chars=3000, citation='Chunk file ' + os.path.basename(f), docname=os.path.basename(f))
            else:
                docs.add(f, chunk_chars=3000)
        except Exception as exception:
            print(exception)
            continue
        pickle.dump(docs, open(lib_dir, "wb"))
    print("Finishing loading papers! Library saved in %s" % os.path.abspath(lib_dir))


def run_qa(lib_name):
    lib_dir = "./saved_libs/" + lib_name + ".pkl"
    docs = pickle.load(open(lib_dir, "rb"))
    question = ""
    while True:
        question = input("Ask something or type 'exit': ")
        while not question:
            print("Question should not be empty!")
            question = input("Ask something or type 'exit': ")
        if question == "exit":
            break
        answer = docs.query(question, k=10, max_sources=10)
        print(answer.formatted_answer)


def run_webqa(lib_name, port):
    import pywebio
    import threading
    import gc
    import nest_asyncio

    nest_asyncio.apply()
    gc.collect()

    lib_dir = "./saved_libs/" + lib_name + ".pkl"
    docs = pickle.load(open(lib_dir, "rb"))

    @pywebio.config(title="Delt4: PaperQA beta")
    def app():
        pywebio.output.put_markdown("## Delt4: Aging PaperQA beta")
        pywebio.output.put_markdown("Lib name: %s" % lib_name)

        answer = None
        evt = threading.Event()

        def get_answer():
            nonlocal answer
            nonlocal evt
            answer = "Waiting for PaperQA..."
            answer = docs.query(question, k=10, max_sources=10).formatted_answer
            evt.set()

        while True:
            answer = None
            evt = threading.Event()
            question = pywebio.input.input(
                "Question", placeholder="Enter your question", required=True
            )
            thread = threading.Thread(target=get_answer)
            thread.start()
            with pywebio.output.use_scope("pending"):
                pywebio.output.put_table([["Q", question], ["A", answer]])
            while True:
                if evt.is_set():
                    break
            pywebio.output.remove(scope="pending")
            pywebio.output.put_table([["Q", question], ["A", answer]])

    pywebio.start_server(app, port=port)


if __name__ == "__main__":
    args = get_arguments()
    if args.lib_name is None:
        raise ValueError("Please specify a new or existing library name.")
    if args.load is not None:
        args.lib_name = format_filename(args.lib_name)
        load_papers(args.load, args.lib_name, args.embeddings)
    elif args.web:
        run_webqa(args.lib_name, args.port)
    else:
        run_qa(args.lib_name)
