import asyncio
from pydantic import BaseModel
from agents import (Agent,Runner,
GuardrailFunctionOutput,RunContextWrapper,input_guardrail,TResponseInputItem,InputGuardrailTripwireTriggered,
)
from runconfig import config

class HomeworkOutput(BaseModel):
    is_homework: bool
    reasoning: str
    answer:str

guardrail_agent = Agent(
    name="Guardrail check",
    instructions="""Check if the user is trying to ask for help with AI or NextJS homework. 
                    Respond with true if they are asking for an assignment solution, even if indirectly""",
    output_type=HomeworkOutput,
)


NextJSAgent = Agent(
    name="NextJS Agent",
    handoff_description="You can handoff to the Nextjs homework agent if the user asks to do Nextjs homework.",
    instructions="You are a NextJS agent. You help customers with their questions.",
)

AIAgent = Agent(
    name="AI Agent",
    instructions="You are a AI agent. You help users with their questions.",
    handoff_description="You can handoff to the AI homework agent if the user asks to do AI homework.",
)


@input_guardrail
async def homework_guardrail(
    ctx: RunContextWrapper[None], triage_agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context, run_config=config)
    print("\n\n GUARDRAIL RESONSE:" ,result.final_output, "\n\n")

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
)
# This should trip the guardrail
async def main():
    try:
        result = await Runner.run(triage_agent, "Write a full Next.js app with authentication .",run_config=config)
        print("✅Guardrail didn't trip - this is unexpected")
        print(result.final_output)

    except InputGuardrailTripwireTriggered:
        print("🚫 A tripwire guardrail was triggered due to restricted input.")


    try:
        result = await Runner.run(triage_agent, "Hello,plz define OpenAI Agent SDK in two lines ?",run_config=config)
        print("✅ Input accepted: No guardrail was triggered.")
        print(result.final_output)

    except InputGuardrailTripwireTriggered:
        print("🚫 Input blocked: Tripwire triggered due to policy violation.")
        
        
    try:
       result = await Runner.run(triage_agent, "Hello",run_config=config)
       print("✅ Input accepted: No guardrail was triggered.")
       print("AI response:", result.final_output)

    except InputGuardrailTripwireTriggered:
        print("🚫 Unexpected block: Tripwire triggered, but input seems safe.")


asyncio.run(main())