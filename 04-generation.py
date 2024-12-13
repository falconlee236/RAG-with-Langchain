import dotenv
import bs4
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


if __name__=="__main__":
    dotenv.load_dotenv()
    
    # load blog
    loader = WebBaseLoader(
        web_paths=(
            "https://lilianweng.github.io/posts/2023-06-23-agent/",
            "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
        ),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer(
                class_=("post-content", "post-title", "post-header")
            )
        ),
    )
    blog_docs = loader.load()
    
    # split
    text_spliter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=300,
        chunk_overlap=50
    )
    
    # make splits
    splits = text_spliter.split_documents(blog_docs)
        
    # Vectorstores - indexing
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=GoogleGenerativeAIEmbeddings(model="models/text-embedding-004"),
    )
    
    retriever = vectorstore.as_retriever(
        search_kwargs=dict(
            k=5, # 이러면 가장 가까운 5개만 가져옴
        )
    )
    
    docs = retriever.get_relevant_documents("What is Task Decomposition?")
    
    # user based Prompt
    template = """Answer the question based only on the following context:
	{context}

	Question: {question}
	"""
    
    prompt = ChatPromptTemplate.from_template(template)
    print(prompt)
    print("--------")
    
    # LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0,
    )
    
    # chain
    chain = prompt | llm
    
    # run
    chain.invoke(dict(
        context=docs,
        question="What is Task Decomposition?",
    ))
    
    # prompt from hub
    prompt_hub_rag = hub.pull("rlm/rag-prompt")
    print(prompt_hub_rag)
    print("---------")
    
    # RAG Chains
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    print(rag_chain.invoke("What is Task Decomposition?"))