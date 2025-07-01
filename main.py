import os
import asyncio
from pydantic import BaseModel
from agents import (Agent,AsyncOpenAI,OpenAIChatCompletionsModel,Runner,
GuardrailFunctionOutput,RunContextWrapper,input_guardrail,TResponseInputItem,InputGuardrailTripwireTriggered
)
from agents.run import RunConfig
from dotenv import load_dotenv ,find_dotenv

load_dotenv(find_dotenv())

gemini_api_key = os.getenv("GEMINI_API_KEY")

provider=AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"

)
model=OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client= provider
)

run_config=RunConfig(
    model=model,
    model_provider= provider,
    tracing_disabled=True
)

class HomeworkOutput(BaseModel):
    is_homework: bool
    reasoning: str
    answer:str

guardrail_agent = Agent(
    name="Guardrail check",
    instructions="""Check if the user is trying to ask for help with AI or NextJS homework. 
                    Respond with true if they are asking for an assignment solution, even if indirectly""",
    output_type=HomeworkOutput,
    model=model
)


NextJSAgent = Agent(
    name="NextJS Agent",
    handoff_description="You can handoff to the Nextjs homework agent if the user asks to do Nextjs homework.",
    instructions="You are a NextJS agent. You help customers with their questions.",
    model=model
)

AIAgent = Agent(
    name="AI Agent",
    instructions="You are a AI agent. You help users with their questions.",
    handoff_description="You can handoff to the AI homework agent if the user asks to do AI homework.",
    model=model
)


@input_guardrail
async def homework_guardrail(
    ctx: RunContextWrapper[None], triage_agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        # tripwire_triggered=False #result.final_output.is_homework,
        tripwire_triggered=result.final_output.is_homework,
    )
triage_agent = Agent(
    name="Triage agent",
    instructions="you determine which agent to use based on the user's question.",
    handoffs=[NextJSAgent ,AIAgent],
    input_guardrails=[homework_guardrail],
    model=model
)
# This should trip the guardrail
async def main():
    try:
        result = await Runner.run(triage_agent, "Hello,plz definne OpenAI Agent SDK in two lines ?")
        print("Guardrail didn't trip - this is unexpected")
        print(result.final_output)

    except InputGuardrailTripwireTriggered:
        print("AI homework guardrail tripped")
    # try:
    #     result = await Runner.run(triage_agent, "Hello")
    #     print(result.final_output)

    # except InputGuardrailTripwireTriggered:
    #     print("AI homework guardrail tripped")
   

asyncio.run(main())