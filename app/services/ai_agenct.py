from langchain.agents import AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
import requests
from typing import List, Dict
import os
import re
import uuid
import json
import dotenv
import logging
from app.core.logging_config import logger
from app.core.config import config_provider
from app.core.cache import RedisCache, cache_response

dotenv.load_dotenv()

class GitHubPRReviewAgent:
    """
    A class to analyze and review GitHub pull requests using LangChain and OpenAI.
    
    This agent performs automated code reviews by analyzing diffs for:
    - Code quality issues
    - Potential bugs
    - Security concerns
    - Best practices
    - Performance issues

    Attributes:
        llm: ChatOpenAI instance for language processing
        tools: List of analysis tools available to the agent
        agent_executor: LangChain agent executor instance
    """

    def __init__(self):
        """
        Initialize the PR review agent with necessary components and configurations.
        Sets up OpenAI API key, language model, tools, and agent executor.
        """
        logger.info("Initializing GitHubPRReviewAgent")
        os.environ['OPENAI_API_KEY'] = config_provider.get_openai_key()
        self.llm = ChatOpenAI(temperature=0.3)
        self.tools = self._setup_tools()
        self.agent_executor = self._setup_agent()
        self.cache = RedisCache()
        logger.info("GitHubPRReviewAgent initialization complete")

    @cache_response(prefix="diff_content", ttl=3600)
    def _fetch_diff_content(self, diff_url: str) -> str:
        """
        Fetch the diff content from a given URL.

        Args:
            diff_url (str): URL of the diff to fetch

        Returns:
            str: Content of the diff or error message if fetch fails
        """
        logger.info(f"Fetching diff content from URL: {diff_url}")
        try:
            response = requests.get(diff_url)
            response.raise_for_status()
            logger.debug(f"Successfully fetched diff content of size: {len(response.text)} bytes")
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching diff content: {str(e)}")
            return f"Error fetching diff: {str(e)}"

    def _parse_diff(self, diff_content: str) -> List[Dict]:
        """
        Parse the diff content into a structured format.

        Args:
            diff_content (str): Raw diff content

        Returns:
            List[Dict]: List of dictionaries containing filename and diff content
        """
        logger.debug("Starting diff parsing")
        files = []
        current_file = None
        current_diff = []
        
        try:
            for line in diff_content.split('\n'):
                if line.startswith('diff --git'):
                    if current_file:
                        files.append({
                            'filename': current_file,
                            'diff': '\n'.join(current_diff)
                        })
                    current_file = line.split(' b/')[-1]
                    current_diff = [line]
                    logger.debug(f"Processing file: {current_file}")
                elif current_file:
                    current_diff.append(line)
            
            if current_file:
                files.append({
                    'filename': current_file,
                    'diff': '\n'.join(current_diff)
                })
            
            logger.info(f"Successfully parsed {len(files)} files from diff")
            return files
        except Exception as e:
            logger.error(f"Error parsing diff content: {str(e)}")
            raise

    def _extract_line_number(self, diff_line: str) -> int:
        """
        Extract line number from a diff line.

        Args:
            diff_line (str): Line from the diff content

        Returns:
            int: Extracted line number or 0 if not found
        """
        try:
            match = re.search(r'\+(\d+)', diff_line)
            return int(match.group(1)) if match else 0
        except Exception as e:
            logger.error(f"Error extracting line number from diff line: {str(e)}")
            return 0

    def _analyze_diff_for_issues(self, diff_content: str) -> List[Dict]:
        """
        Analyze diff content for common code issues.

        Args:
            diff_content (str): Content of the diff to analyze

        Returns:
            List[Dict]: List of identified issues with their details
        """
        logger.debug("Starting diff analysis for issues")
        issues = []
        lines = diff_content.split('\n')
        current_line = 0
        
        try:
            for line in lines:
                if line.startswith('+'):
                    current_line = self._extract_line_number(line) or current_line + 1
                    
                    if len(line) > 100:
                        logger.debug(f"Found long line issue at line {current_line}")
                        issues.append({
                            "type": "style",
                            "line": current_line,
                            "description": "Line exceeds recommended length of 100 characters",
                            "suggestion": "Consider breaking this line into multiple lines"
                        })
                    
                    if 'TODO' in line:
                        logger.debug(f"Found TODO comment at line {current_line}")
                        issues.append({
                            "type": "maintenance",
                            "line": current_line,
                            "description": "TODO comment found",
                            "suggestion": "Implement the TODO or create a ticket for tracking"
                        })
            
            logger.info(f"Found {len(issues)} issues in diff analysis")
            return issues
        except Exception as e:
            logger.error(f"Error analyzing diff for issues: {str(e)}")
            raise

    def _setup_tools(self) -> List[Tool]:
        """
        Set up the analysis tools available to the agent.

        Returns:
            List[Tool]: List of LangChain tools for different types of analysis
        """
        logger.debug("Setting up agent tools")
        tools = [
            Tool(
                name="analyze_code_changes",
                func=self._analyze_code_changes,
                description="Analyzes code changes in the PR diff and provides feedback"
            ),
            Tool(
                name="analyze_best_practices",
                func=self._analyze_best_practices,
                description="Analyzes code against programming best practices"
            ),
            Tool(
                name="security_review",
                func=self._security_review,
                description="Performs a security review of the changes"
            )
        ]
        logger.info(f"Successfully set up {len(tools)} tools")
        return tools

    def _setup_agent(self) -> AgentExecutor:
        """
        Set up the LangChain agent executor with the necessary prompt template.

        Returns:
            AgentExecutor: Configured agent executor instance
        """
        logger.debug("Setting up agent executor")
        template = """Analyze the following pull request diff and provide a detailed review in JSON format. Focus on:
1. Code quality issues
2. Potential bugs
3. Security concerns
4. Best practices
5. Performance issues

Use the following format:
Question: the input question you must answer
Thought: consider what aspects to analyze
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know what issues to report
Final Answer: Provide the analysis in a structured format that can be converted to JSON

{tools}

Question: {input}

{agent_scratchpad}"""

        try:
            prompt = PromptTemplate(
                template=template,
                input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
            )

            agent = create_react_agent(self.llm, self.tools, prompt)
            executor = AgentExecutor.from_agent_and_tools(
                agent=agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                return_intermediate_steps=True
            )
            logger.info("Successfully set up agent executor")
            return executor
        except Exception as e:
            logger.error(f"Error setting up agent executor: {str(e)}")
            raise

    def _analyze_code_changes(self, diff_url: str) -> str:
        """
        Analyze code changes from a diff URL.

        Args:
            diff_url (str): URL of the diff to analyze

        Returns:
            str: JSON string containing analysis results
        """
        logger.info(f"Starting code changes analysis for {diff_url}")
        try:
            diff_content = self._fetch_diff_content(diff_url)
            files = self._parse_diff(diff_content)
            
            results = []
            for file in files:
                issues = self._analyze_diff_for_issues(file['diff'])
                result = {
                    "filename": file['filename'],
                    "issues": issues
                }
                results.append(result)
            
            logger.info(f"Completed code changes analysis with {len(results)} file results")
            return json.dumps(results)
        except Exception as e:
            logger.error(f"Error in code changes analysis: {str(e)}")
            raise

    def _analyze_best_practices(self, diff_url: str) -> str:
        """
        Analyze code changes for best practices compliance.

        Args:
            diff_url (str): URL of the diff to analyze

        Returns:
            str: JSON string containing best practices analysis results
        """
        logger.info(f"Starting best practices analysis for {diff_url}")
        try:
            diff_content = self._fetch_diff_content(diff_url)
            prompt = self.llm.predict(f"""Analyze these changes for best practices issues. Return a JSON array of issues:
            {diff_content}
            
            Format each issue as:
            {{
                "type": "best_practice",
                "line": <line_number>,
                "description": <issue_description>,
                "suggestion": <improvement_suggestion>
            }}
            """)
            logger.info("Completed best practices analysis")
            return prompt
        except Exception as e:
            logger.error(f"Error in best practices analysis: {str(e)}")
            raise

    def _security_review(self, diff_url: str) -> str:
        """
        Perform security review of code changes.

        Args:
            diff_url (str): URL of the diff to analyze

        Returns:
            str: JSON string containing security analysis results
        """
        logger.info(f"Starting security review for {diff_url}")
        try:
            diff_content = self._fetch_diff_content(diff_url)
            prompt = self.llm.predict(f"""Analyze these changes for security issues. Return a JSON array of issues:
            {diff_content}
            
            Format each issue as:
            {{
                "type": "security",
                "line": <line_number>,
                "description": <security_issue_description>,
                "suggestion": <security_improvement_suggestion>
            }}
            """)
            logger.info("Completed security review")
            return prompt
        except Exception as e:
            logger.error(f"Error in security review: {str(e)}")
            raise

    def _format_results(self, analysis_results: List[Dict], diff_url: str) -> Dict:
        """
        Format analysis results into a structured output.

        Args:
            analysis_results (List[Dict]): Raw analysis results
            diff_url (str): URL of the analyzed diff

        Returns:
            Dict: Structured results with summary statistics
        """
        logger.debug("Starting to format analysis results")
        try:
            files_data = []
            total_issues = 0
            critical_issues = 0
            
            diff_content = self._fetch_diff_content(diff_url)
            files = self._parse_diff(diff_content)
            
            for file in files:
                file_issues = []
                for result in analysis_results:
                    if isinstance(result, str):
                        try:
                            parsed_result = json.loads(result)
                            if isinstance(parsed_result, list):
                                for issue in parsed_result:
                                    if isinstance(issue, dict) and 'type' in issue:
                                        file_issues.append(issue)
                                        total_issues += 1
                                        if issue['type'] in ['security', 'bug']:
                                            critical_issues += 1
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse result as JSON: {result[:100]}...")
                            continue
                
                files_data.append({
                    "name": file['filename'],
                    "issues": file_issues
                })
            
            formatted_results = {
                "files": files_data,
                "summary": {
                    "total_files": len(files),
                    "total_issues": total_issues,
                    "critical_issues": critical_issues   
                }
            }
            
            logger.info(f"Results formatted: {total_issues} total issues, {critical_issues} critical issues")
            return formatted_results
        except Exception as e:
            logger.error(f"Error formatting results: {str(e)}")
            raise

    @cache_response(prefix="pr_review", ttl=7200)  # Cache for 2 hours
    def review_pr(self, diff_url: str) -> Dict:
        """
        Review a pull request and provide comprehensive analysis.

        This method orchestrates the entire PR review process, including:
        - Fetching and parsing the diff
        - Running various analyses (code quality, security, best practices)
        - Formatting and summarizing results

        Args:
            diff_url (str): URL of the PR diff to review

        Returns:
            Dict: Structured review results including all issues found and summary statistics

        Raises:
            Exception: If any step of the review process fails
        """
        logger.info(f"Starting PR review for {diff_url}")
        try:
            result = self.agent_executor.invoke(
                {"input": f"Review the pull request diff at {diff_url}"}
            )
            
            analysis_results = [step[1] for step in result.get('intermediate_steps', [])]
            formatted_results = self._format_results(analysis_results, diff_url)
            
            logger.info("PR review completed successfully")
            return formatted_results
        except Exception as e:
            logger.error(f"Error during PR review: {str(e)}")
            raise


reviewer = GitHubPRReviewAgent()