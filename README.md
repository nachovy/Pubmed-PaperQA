# Pubmed-PaperQA
Tools for searching for [PubMed](https://pubmed.ncbi.nlm.nih.gov/) papers and building question-answering language models based on [paper-qa](https://github.com/whitead/paper-qa).

Clone the repository
    
    git clone git@github.com:nachovy/Pubmed-PaperQA.git

Install required packages and dependencies

    pip install -r requirements.txt

# Get papers

### Search papers by keywords

Search papers from pubmed using [NCBIQuery](https://github.com/nachovy/NCBIQuery), and store result paper pmids in './paper_ids.txt'

    python -m papertool.search --keyword aging

With more options

    python -m papertool.search --keyword aging --type review --date 1990/01/01:2023/01/01 --retmax 1000
    
Date should be 'YYYY/MM/DD:YYYY/MM/DD' format, and retmax is the maximum number of papers returned, with default value 10,000.

The option -a or --add will append the new results to './paper_ids.txt' instead of overwriting it

    python -m papertool.search -a --keyword aging

Searching for paper containing multiple keywords, but try using "AND" for delimiters

    python -m papertool.search --keyword aging AND lung cancer

### Search papers by question

Another option is using the question you are asking to generate keywords and search papers. This function will apply the language model GPT-3.5-turbo, so you will need to add your OPENAI_API_KEY first. It is better to append this script into '~/.bashrc'.

    export OPENAI_API_KEY=...
    python -m papertool.search --question What is the biggest mystery of aging field?

Resulting keywords will be displayed. You can also do another search based on these generated keywords.

### Download papers 

Get full text papers using a modified copy of [PubMed2PDF](https://github.com/ddomingof/PubMed2PDF/) and [scihub.py](https://github.com/zaytoun/scihub.py). Papers will be saved in default directory './saved_papers'.

    python -m papertool.download

Or with specified text file with paper pmids

    python -m papertool.download --id_file /path/to/id.txt

Or one specified pmid

    python -m papertool.download --id 10793553
    
Specify the output folder

    python -m papertool.download --output_dir /path/to/paper/dir

If you only want abstracts from the papers, that will be easier since they can be directly retrieved from PubMed. Abstracts will be saved as .txt files. Because there is an API rate limit of PubMed query, you may need to run the same script multiple times to retrieve all abstracts.

    python -m papertool.download --abstract

# Load papers

Load all the papers we got into a library instance ([paperqa.Docs](https://github.com/whitead/paper-qa/blob/main/paperqa/docs.py) module). By default, the embedding model is [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) and the large language model is GPT-3.5-turbo.
 
Add OpenAI API Key to system environment variables. It is better to append this script into '~/.bashrc'

    export OPENAI_API_KEY=...
    
Load papers to a new library

    python -m qatool.qa --load --lib_name new_lib
    
This will load papers from default directory './saved_papers'. You can also specify the paper directory

    python -m qatool.qa --load /path/to/paper/dir --lib_name new_lib

Or single paper file

    python -m qatool.qa --load paper.pdf --lib_name new_lib
    
Then a pkl format library file will be saved in saved_libs directory. If a library with that name already exists, papers will be added to the old library file without overwriting it

You can specify the embedding model used, by default it will use [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2)

    python -m qatool.qa --load --lib_name new_lib --embeddings microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext

# Run command line QA tool

    python -m qatool.qa --run --lib_name new_lib
    
Omitting the --run argument also works
 
    python -m qatool.qa --lib_name new_lib
    
It will load the library file saved in './saved_libs/new_lib.pkl'. Type your questions and wait for the answer. Type 'exit' to stop.

Sometimes the initial answer will take a lot of time, depending on the amount of papers the library contains. But it will run fast on later questions.

# Run webpage QA tool

    python -m qatool.qa --web --lib_name new_lib

Then visit http://localhost from your browser. If you are running on a server, replace localhost with server's public ip address

You can also specify which port to use

    python -m qatool.qa --web --lib_name new_lib --port 8000

Now it is run on http://localhost:8000 instead.

# Embedding interface

There is an intermediate interface ```get_embeddings(doc_dir, embeddings_name)``` of getting all chunked texts with their corresponding embedding vectors. 

Arguments:
| Parameter                 | Default       | Description   |   
| :------------------------ |:-------------:| :-------------|
| doc_dir           |               |  Path to paper directory or single paper file |
| embeddings_name          | all-mpnet-base-v2           | Name of embedding model |

Return: Two lists containing strings of chunked documents and embedding vectors.

Here is an example of usage in python:

```python
from qatool.qa import get_embeddings
import numpy
texts, embeddings = get_embeddings('/path/to/paper/dir/or/single/paper/file', 'all-mpnet-base-v2')
print(numpy.array(embeddings[0]).shape)
# (768,)
```

If embeddings_name is None or empty, it will return an empty list for embeddings.

```python
from qatool.qa import get_embeddings
texts, embeddings = get_embeddings('/path/to/paper/dir/or/single/paper/file', '')
```

Another similar function with same parameters ```get_embeddings_with_source(doc_dir, embeddings_name)``` is for getting chunked texts and embeddings with corresponding file names. It will return two list of tuples ```(file_name, documents_chunk)``` and ```(file_name, embeddings_chunk)```.

```python
from qatool.qa import get_embeddings_with_source
import numpy
texts, embeddings = get_embeddings_with_source('/path/to/paper/dir/or/single/paper/file', 'all-mpnet-base-v2')
print(texts[0][0])
# /path/.../paper1.pdf
print(texts[0][1])
# PAPER 1 TEXT...
print(embeddings[0][0])
# /path/.../paper1.pdf
print(numpy.array(embeddings[0][1]).shape)
# 768
```