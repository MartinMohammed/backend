SYSTEM_PROMPT_GENERATE = """
    Your are a character in a fantasy world. Your role to help the user find information about you.

    The user will ask questions about you and you will provide the answers.

    
"""

USER_PROMPT_GENERATE = """

{question}
"""

SYSTEM_PROMPT_KNOWLEDGE = """
"""

USER_PROMPT_KNOWLEDGE = """
{history}
"""

SYSTEM_PROMPT_HINT = """
Instructions:
{history}


"""

USER_PROMPT_HINT = """
"""
