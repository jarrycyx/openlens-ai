"""Paper search tools for LangGraph agents."""

import os
from typing import List, Dict, Optional, Type
from functools import wraps

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from datetime import datetime

from .paper_search_mcp.academic_platforms.arxiv import ArxivSearcher
from .paper_search_mcp.academic_platforms.pubmed import PubMedSearcher
from .paper_search_mcp.academic_platforms.biorxiv import BioRxivSearcher
from .paper_search_mcp.academic_platforms.medrxiv import MedRxivSearcher
from .paper_search_mcp.academic_platforms.google_scholar import GoogleScholarSearcher
from .paper_search_mcp.academic_platforms.iacr import IACRSearcher
from .paper_search_mcp.academic_platforms.semantic import SemanticSearcher
from .paper_search_mcp.paper import Paper

arxiv_searcher = ArxivSearcher()
pubmed_searcher = PubMedSearcher()
biorxiv_searcher = BioRxivSearcher()
medrxiv_searcher = MedRxivSearcher()
google_scholar_searcher = GoogleScholarSearcher()
iacr_searcher = IACRSearcher()
semantic_searcher = SemanticSearcher()


def sync_to_async(func):
    import asyncio
    import functools

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

    return async_wrapper


class SearchArxivInput(BaseModel):
    """Input arguments for searching papers on arXiv"""

    query: str = Field(..., description="Search query string (e.g., 'machine learning')")
    max_results: int = Field(10, description="Maximum number of papers to return (default: 10)")


class SearchArxivTool(BaseTool):
    """Tool for searching academic papers from arXiv database"""

    name: str = "search_arxiv_tool"
    description: str = (
        "Search for academic papers on arXiv.org based on a query string. Returns paper metadata including title, authors, abstract, and other details."
    )
    args_schema: Type[BaseModel] = SearchArxivInput

    def _run(self, query: str, max_results: int = 10) -> List[Dict]:
        """Execute arXiv search"""
        papers = arxiv_searcher.search(query, max_results=max_results)
        return [paper.to_dict() for paper in papers] if papers else []

    async def _arun(self, query: str, max_results: int = 10) -> List[Dict]:
        """Asynchronously execute arXiv search"""
        return await sync_to_async(self._run)(query, max_results)


class SearchPubMedInput(BaseModel):
    """Input arguments for searching papers on PubMed"""

    query: str = Field(..., description="Search query string (e.g., 'cancer research')")
    max_results: int = Field(10, description="Maximum number of papers to return (default: 10)")


class SearchPubMedTool(BaseTool):
    """Tool for searching academic papers from PubMed database"""

    name: str = "search_pubmed_tool"
    description: str = (
        "Search for academic papers on PubMed based on a query string. Returns paper metadata including title, authors, abstract, and other details."
    )
    args_schema: Type[BaseModel] = SearchPubMedInput

    def _run(self, query: str, max_results: int = 10) -> List[Dict]:
        """Execute PubMed search"""
        papers = pubmed_searcher.search(query, max_results=max_results)
        return [paper.to_dict() for paper in papers] if papers else []

    async def _arun(self, query: str, max_results: int = 10) -> List[Dict]:
        """Asynchronously execute PubMed search"""
        return await sync_to_async(self._run)(query, max_results)


class SearchBioRxivInput(BaseModel):
    """Input arguments for searching papers on bioRxiv"""

    query: str = Field(..., description="Search query string (e.g., 'genomics')")
    max_results: int = Field(10, description="Maximum number of papers to return (default: 10)")


class SearchBioRxivTool(BaseTool):
    """Tool for searching academic papers from bioRxiv database"""

    name: str = "search_biorxiv_tool"
    description: str = (
        "Search for academic papers on bioRxiv (biology preprint server) based on a query string. Returns paper metadata including title, authors, abstract, and other details."
    )
    args_schema: Type[BaseModel] = SearchBioRxivInput

    def _run(self, query: str, max_results: int = 10) -> List[Dict]:
        """Execute bioRxiv search"""
        papers = biorxiv_searcher.search(query, max_results=max_results)
        return [paper.to_dict() for paper in papers] if papers else []

    async def _arun(self, query: str, max_results: int = 10) -> List[Dict]:
        """Asynchronously execute bioRxiv search"""
        return await sync_to_async(self._run)(query, max_results)


class SearchMedRxivInput(BaseModel):
    """Input arguments for searching papers on medRxiv"""

    query: str = Field(..., description="Search query string (e.g., 'clinical trial')")
    max_results: int = Field(10, description="Maximum number of papers to return (default: 10)")


class SearchMedRxivTool(BaseTool):
    """Tool for searching academic papers from medRxiv database"""

    name: str = "search_medrxiv_tool"
    description: str = (
        "Search for academic papers on medRxiv (medical preprint server) based on a query string. Returns paper metadata including title, authors, abstract, and other details."
    )
    args_schema: Type[BaseModel] = SearchMedRxivInput

    def _run(self, query: str, max_results: int = 10) -> List[Dict]:
        """Execute medRxiv search"""
        papers = medrxiv_searcher.search(query, max_results=max_results)
        return [paper.to_dict() for paper in papers] if papers else []

    async def _arun(self, query: str, max_results: int = 10) -> List[Dict]:
        """Asynchronously execute medRxiv search"""
        return await sync_to_async(self._run)(query, max_results)


class SearchGoogleScholarInput(BaseModel):
    """Input arguments for searching papers on Google Scholar"""

    query: str = Field(..., description="Search query string (e.g., 'neural networks')")
    max_results: int = Field(10, description="Maximum number of papers to return (default: 10)")


class SearchGoogleScholarTool(BaseTool):
    """Tool for searching academic papers from Google Scholar"""

    name: str = "search_google_scholar_tool"
    description: str = (
        "Search for academic papers on Google Scholar based on a query string. Returns paper metadata including title, authors, abstract, and other details."
    )
    args_schema: Type[BaseModel] = SearchGoogleScholarInput

    def _run(self, query: str, max_results: int = 10) -> List[Dict]:
        """Execute Google Scholar search"""
        papers = google_scholar_searcher.search(query, max_results=max_results)
        return [paper.to_dict() for paper in papers] if papers else []

    async def _arun(self, query: str, max_results: int = 10) -> List[Dict]:
        """Asynchronously execute Google Scholar search"""
        return await sync_to_async(self._run)(query, max_results)


class SearchIACRInput(BaseModel):
    """Input arguments for searching papers on IACR ePrint Archive"""

    query: str = Field(..., description="Search query string (e.g., 'cryptography', 'secret sharing')")
    max_results: int = Field(10, description="Maximum number of papers to return (default: 10)")
    fetch_details: bool = Field(True, description="Whether to fetch detailed information for each paper (default: True)")


class SearchIACRTool(BaseTool):
    """Tool for searching academic papers from IACR ePrint Archive"""

    name: str = "search_iacr_tool"
    description: str = (
        "Search for academic papers on IACR ePrint Archive (International Association for Cryptologic Research) based on a query string. Returns paper metadata including title, authors, abstract, and other details."
    )
    args_schema: Type[BaseModel] = SearchIACRInput

    def _run(self, query: str, max_results: int = 10, fetch_details: bool = True) -> List[Dict]:
        """Execute IACR search"""
        papers = iacr_searcher.search(query, max_results=max_results, fetch_details=fetch_details)
        return [paper.to_dict() for paper in papers] if papers else []

    async def _arun(self, query: str, max_results: int = 10, fetch_details: bool = True) -> List[Dict]:
        """Asynchronously execute IACR search"""
        return await sync_to_async(self._run)(query, max_results, fetch_details)


class SearchSemanticInput(BaseModel):
    """Input arguments for searching papers on Semantic Scholar"""

    query: str = Field(..., description="Search query string (e.g., 'machine learning')")
    year: Optional[str] = Field(None, description="Optional year filter (e.g., '2019', '2016-2020', '2010-', '-2015')")
    max_results: int = Field(10, description="Maximum number of papers to return (default: 10)")


class SearchSemanticTool(BaseTool):
    """Tool for searching academic papers from Semantic Scholar"""

    name: str = "search_semantic_tool"
    description: str = (
        "Search for academic papers on Semantic Scholar based on a query string with optional year filtering. Returns paper metadata including title, authors, abstract, citation count, and other details."
    )
    args_schema: Type[BaseModel] = SearchSemanticInput

    def _run(self, query: str, year: Optional[str] = None, max_results: int = 10) -> List[Dict]:
        """Execute Semantic Scholar search"""
        if year is not None:
            papers = semantic_searcher.search(query, year=year, max_results=max_results)
        else:
            papers = semantic_searcher.search(query, max_results=max_results)
        return [paper.to_dict() for paper in papers] if papers else []

    async def _arun(self, query: str, year: Optional[str] = None, max_results: int = 10) -> List[Dict]:
        """Asynchronously execute Semantic Scholar search"""
        return await sync_to_async(self._run)(query, year, max_results)


class DownloadArxivInput(BaseModel):
    """Input arguments for downloading arXiv papers"""

    paper_id: str = Field(..., description="arXiv paper ID (e.g., '2106.12345')")
    save_path: str = Field("./downloads", description="Directory to save the PDF (default: './downloads')")


class DownloadArxivTool(BaseTool):
    """Tool for downloading arXiv paper PDFs"""

    name: str = "download_arxiv_tool"
    description: str = "Download PDF of an arXiv paper given its paper ID. The PDF will be saved to the specified path."
    args_schema: Type[BaseModel] = DownloadArxivInput

    def _run(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Download arXiv paper PDF"""
        os.makedirs(save_path, exist_ok=True)
        return arxiv_searcher.download_pdf(paper_id, save_path)

    async def _arun(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Asynchronously download arXiv paper PDF"""
        return await sync_to_async(self._run)(paper_id, save_path)


class DownloadPubMedInput(BaseModel):
    """Input arguments for downloading PubMed papers"""

    paper_id: str = Field(..., description="PubMed ID (PMID)")
    save_path: str = Field("./downloads", description="Directory to save the PDF (default: './downloads')")


class DownloadPubMedTool(BaseTool):
    """Tool for attempting to download PubMed paper PDFs"""

    name: str = "download_pubmed_tool"
    description: str = "Attempt to download PDF of a PubMed paper given its PMID. Note that direct PDF download may not be supported for all papers."
    args_schema: Type[BaseModel] = DownloadPubMedInput

    def _run(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Attempt to download PubMed paper PDF"""
        try:
            os.makedirs(save_path, exist_ok=True)
            return pubmed_searcher.download_pdf(paper_id, save_path)
        except NotImplementedError as e:
            return str(e)

    async def _arun(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Asynchronously attempt to download PubMed paper PDF"""
        return await sync_to_async(self._run)(paper_id, save_path)


class DownloadBioRxivInput(BaseModel):
    """Input arguments for downloading bioRxiv papers"""

    paper_id: str = Field(..., description="bioRxiv DOI")
    save_path: str = Field("./downloads", description="Directory to save the PDF (default: './downloads')")


class DownloadBioRxivTool(BaseTool):
    """Tool for downloading bioRxiv paper PDFs"""

    name: str = "download_biorxiv_tool"
    description: str = "Download PDF of a bioRxiv paper given its DOI. The PDF will be saved to the specified path."
    args_schema: Type[BaseModel] = DownloadBioRxivInput

    def _run(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Download bioRxiv paper PDF"""
        os.makedirs(save_path, exist_ok=True)
        return biorxiv_searcher.download_pdf(paper_id, save_path)

    async def _arun(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Asynchronously download bioRxiv paper PDF"""
        return await sync_to_async(self._run)(paper_id, save_path)


class DownloadMedRxivInput(BaseModel):
    """Input arguments for downloading medRxiv papers"""

    paper_id: str = Field(..., description="medRxiv DOI")
    save_path: str = Field("./downloads", description="Directory to save the PDF (default: './downloads')")


class DownloadMedRxivTool(BaseTool):
    """Tool for downloading medRxiv paper PDFs"""

    name: str = "download_medrxiv_tool"
    description: str = "Download PDF of a medRxiv paper given its DOI. The PDF will be saved to the specified path."
    args_schema: Type[BaseModel] = DownloadMedRxivInput

    def _run(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Download medRxiv paper PDF"""
        os.makedirs(save_path, exist_ok=True)
        return medrxiv_searcher.download_pdf(paper_id, save_path)

    async def _arun(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Asynchronously download medRxiv paper PDF"""
        return await sync_to_async(self._run)(paper_id, save_path)


class DownloadIACRInput(BaseModel):
    """Input arguments for downloading IACR papers"""

    paper_id: str = Field(..., description="IACR paper ID (e.g., '2009/101')")
    save_path: str = Field("./downloads", description="Directory to save the PDF (default: './downloads')")


class DownloadIACRTool(BaseTool):
    """Tool for downloading IACR ePrint paper PDFs"""

    name: str = "download_iacr_tool"
    description: str = "Download PDF of an IACR ePrint paper given its paper ID. The PDF will be saved to the specified path."
    args_schema: Type[BaseModel] = DownloadIACRInput

    def _run(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Download IACR paper PDF"""
        os.makedirs(save_path, exist_ok=True)
        return iacr_searcher.download_pdf(paper_id, save_path)

    async def _arun(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Asynchronously download IACR paper PDF"""
        return await sync_to_async(self._run)(paper_id, save_path)


class DownloadSemanticInput(BaseModel):
    """Input arguments for downloading Semantic Scholar papers"""

    paper_id: str = Field(
        ...,
        description="Semantic Scholar paper ID, Paper identifier in one of the following formats: "
        '- Semantic Scholar ID (e.g., "649def34f8be52c8b66281af98ae884c09aef38b") '
        '- DOI:<doi> (e.g., "DOI:10.18653/v1/N18-3011") '
        '- ARXIV:<id> (e.g., "ARXIV:2106.15928") '
        '- MAG:<id> (e.g., "MAG:112218234") '
        '- ACL:<id> (e.g., "ACL:W12-3903") '
        '- PMID:<id> (e.g., "PMID:19872477") '
        '- PMCID:<id> (e.g., "PMCID:2323736") '
        '- URL:<url> (e.g., "URL:https://arxiv.org/abs/2106.15928v1")',
    )
    save_path: str = Field("./downloads", description="Directory to save the PDF (default: './downloads')")


class DownloadSemanticTool(BaseTool):
    """Tool for downloading Semantic Scholar paper PDFs"""

    name: str = "download_semantic_tool"
    description: str = "Download PDF of a Semantic Scholar paper given its paper ID in various formats. The PDF will be saved to the specified path."
    args_schema: Type[BaseModel] = DownloadSemanticInput

    def _run(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Download Semantic Scholar paper PDF"""
        os.makedirs(save_path, exist_ok=True)
        return semantic_searcher.download_pdf(paper_id, save_path)

    async def _arun(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Asynchronously download Semantic Scholar paper PDF"""
        return await sync_to_async(self._run)(paper_id, save_path)


class ReadArxivPaperInput(BaseModel):
    """Input arguments for reading arXiv papers"""

    paper_id: str = Field(..., description="arXiv paper ID (e.g., '2106.12345')")
    save_path: str = Field("./downloads", description="Directory where the PDF is/will be saved (default: './downloads')")


class ReadArxivPaperTool(BaseTool):
    """Tool for reading and extracting text content from arXiv paper PDFs"""

    name: str = "read_arxiv_paper_tool"
    description: str = (
        "Read and extract text content from an arXiv paper PDF. The tool will first download the paper if it doesn't exist locally, then extract the text content."
    )
    args_schema: Type[BaseModel] = ReadArxivPaperInput

    def _run(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Read and extract text content from arXiv paper PDF"""
        try:
            return arxiv_searcher.read_paper(paper_id, save_path)
        except Exception as e:
            print(f"Error reading paper {paper_id}: {e}")
            return ""

    async def _arun(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Asynchronously read and extract text content from arXiv paper PDF"""
        return await sync_to_async(self._run)(paper_id, save_path)


class ReadPubMedPaperInput(BaseModel):
    """Input arguments for reading PubMed papers"""

    paper_id: str = Field(..., description="PubMed ID (PMID)")
    save_path: str = Field("./downloads", description="Directory where the PDF would be saved (unused)")


class ReadPubMedPaperTool(BaseTool):
    """Tool for reading and extracting text content from PubMed papers"""

    name: str = "read_pubmed_paper_tool"
    description: str = "Read and extract text content from a PubMed paper. Note that direct paper reading may not be supported for all papers."
    args_schema: Type[BaseModel] = ReadPubMedPaperInput

    def _run(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Read and extract text content from PubMed paper"""
        return pubmed_searcher.read_paper(paper_id, save_path)

    async def _arun(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Asynchronously read and extract text content from PubMed paper"""
        return await sync_to_async(self._run)(paper_id, save_path)


class ReadBioRxivPaperInput(BaseModel):
    """Input arguments for reading bioRxiv papers"""

    paper_id: str = Field(..., description="bioRxiv DOI")
    save_path: str = Field("./downloads", description="Directory where the PDF is/will be saved (default: './downloads')")


class ReadBioRxivPaperTool(BaseTool):
    """Tool for reading and extracting text content from bioRxiv paper PDFs"""

    name: str = "read_biorxiv_paper_tool"
    description: str = (
        "Read and extract text content from a bioRxiv paper PDF. The tool will first download the paper if it doesn't exist locally, then extract the text content."
    )
    args_schema: Type[BaseModel] = ReadBioRxivPaperInput

    def _run(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Read and extract text content from bioRxiv paper PDF"""
        try:
            return biorxiv_searcher.read_paper(paper_id, save_path)
        except Exception as e:
            print(f"Error reading paper {paper_id}: {e}")
            return ""

    async def _arun(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Asynchronously read and extract text content from bioRxiv paper PDF"""
        return await sync_to_async(self._run)(paper_id, save_path)


class ReadMedRxivPaperInput(BaseModel):
    """Input arguments for reading medRxiv papers"""

    paper_id: str = Field(..., description="medRxiv DOI")
    save_path: str = Field("./downloads", description="Directory where the PDF is/will be saved (default: './downloads')")


class ReadMedRxivPaperTool(BaseTool):
    """Tool for reading and extracting text content from medRxiv paper PDFs"""

    name: str = "read_medrxiv_paper_tool"
    description: str = (
        "Read and extract text content from a medRxiv paper PDF. The tool will first download the paper if it doesn't exist locally, then extract the text content."
    )
    args_schema: Type[BaseModel] = ReadMedRxivPaperInput

    def _run(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Read and extract text content from medRxiv paper PDF"""
        try:
            return medrxiv_searcher.read_paper(paper_id, save_path)
        except Exception as e:
            print(f"Error reading paper {paper_id}: {e}")
            return ""

    async def _arun(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Asynchronously read and extract text content from medRxiv paper PDF"""
        return await sync_to_async(self._run)(paper_id, save_path)


class ReadIACRPaperInput(BaseModel):
    """Input arguments for reading IACR papers"""

    paper_id: str = Field(..., description="IACR paper ID (e.g., '2009/101')")
    save_path: str = Field("./downloads", description="Directory where the PDF is/will be saved (default: './downloads')")


class ReadIACRPaperTool(BaseTool):
    """Tool for reading and extracting text content from IACR ePrint paper PDFs"""

    name: str = "read_iacr_paper_tool"
    description: str = (
        "Read and extract text content from an IACR ePrint paper PDF. The tool will first download the paper if it doesn't exist locally, then extract the text content."
    )
    args_schema: Type[BaseModel] = ReadIACRPaperInput

    def _run(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Read and extract text content from IACR paper PDF"""
        try:
            return iacr_searcher.read_paper(paper_id, save_path)
        except Exception as e:
            print(f"Error reading paper {paper_id}: {e}")
            return ""

    async def _arun(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Asynchronously read and extract text content from IACR paper PDF"""
        return await sync_to_async(self._run)(paper_id, save_path)


class ReadSemanticPaperInput(BaseModel):
    """Input arguments for reading Semantic Scholar papers"""

    paper_id: str = Field(
        ...,
        description="Semantic Scholar paper ID, Paper identifier in one of the following formats: "
        '- Semantic Scholar ID (e.g., "649def34f8be52c8b66281af98ae884c09aef38b") '
        '- DOI:<doi> (e.g., "DOI:10.18653/v1/N18-3011") '
        '- ARXIV:<id> (e.g., "ARXIV:2106.15928") '
        '- MAG:<id> (e.g., "MAG:112218234") '
        '- ACL:<id> (e.g., "ACL:W12-3903") '
        '- PMID:<id> (e.g., "PMID:19872477") '
        '- PMCID:<id> (e.g., "PMCID:2323736") '
        '- URL:<url> (e.g., "URL:https://arxiv.org/abs/2106.15928v1")',
    )
    save_path: str = Field("./downloads", description="Directory where the PDF is/will be saved (default: './downloads')")


class ReadSemanticPaperTool(BaseTool):
    """Tool for reading and extracting text content from Semantic Scholar papers"""

    name: str = "read_semantic_paper_tool"
    description: str = (
        "Read and extract text content from a Semantic Scholar paper. The tool will first download the paper if it doesn't exist locally, then extract the text content."
    )
    args_schema: Type[BaseModel] = ReadSemanticPaperInput

    def _run(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Read and extract text content from Semantic Scholar paper"""
        try:
            return semantic_searcher.read_paper(paper_id, save_path)
        except Exception as e:
            print(f"Error reading paper {paper_id}: {e}")
            return ""

    async def _arun(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Asynchronously read and extract text content from Semantic Scholar paper"""
        return await sync_to_async(self._run)(paper_id, save_path)


class DummySearchTool(BaseTool):
    """Tool for searching academic papers from medRxiv database"""

    name: str = "search_tool"
    description: str = "Search for academic papers on web"
    args_schema: Type[BaseModel] = SearchMedRxivInput

    def _run(self, query: str, max_results: int = 10) -> List[Dict]:
        """Execute medRxiv search"""
        papers = [
            Paper(
                paper_id="123",
                title="Paper Title",
                authors=["Author 1", "Author 2"],
                abstract="Paper abstract",
                doi="10.1234/abcdefg",
                published_date=datetime.fromtimestamp(0),
                pdf_url="",
                url="",
                source="",
            )
            for _ in range(max_results)
        ]
        return [paper.to_dict() for paper in papers] if papers else []

    async def _arun(self, query: str, max_results: int = 10) -> List[Dict]:
        """Asynchronously execute medRxiv search"""
        return await sync_to_async(self._run)(query, max_results)
