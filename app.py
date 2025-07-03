import streamlit as st
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
        tripwire_triggered=result.final_output.is_homework,
    )
triage_agent = Agent(
    name="Triage agent",
    instructions="you determine which agent to use based on the user's question.",
    handoffs=[NextJSAgent ,AIAgent],
    input_guardrails=[homework_guardrail],
)
# This should trip the guardrail

# UI
st.set_page_config(page_title="Guardrail Checker" ,layout="centered")
st.title("🚦 Homework Guardrail Checker")
st.markdown("##TRY THREE DIFFERENT QUSETIONS TO CHECK GUARDRAILS")
st.info(
    "Enter:\n"
    "- An AI realated Qusetion \n"
    "- A Next.js assignment request\n"
    "- A normal, safe message\n"
)
col1,col2,col3=st.columns(3)
    
with col1:
        ques1 = st.text_input("Question #2:" ,placeholder="e.g:Define AI shortly?")
with col2:
        ques2= st.text_input("Question #3:" ,placeholder="Build a nextjs login page")
with col3:
        ques3 = st.text_input("Question #1:" ,placeholder= "e.g:Hello,How are you?")
        
    # Async logic
async def process_input(input_text, label):
    try:
        result = await Runner.run(triage_agent, input_text, run_config=config)
        st.success(f"✅ {label}: Input accepted:No Guardrail triggered.")
        st.markdown(f" Response of {label} :")
        st.write(result.final_output)
    except InputGuardrailTripwireTriggered:
        st.error(f"🚫 {label}: Guardrail triggered, blocked input_Tripwire triggered due to policy violation.")

async def run_all_inputs():
    if ques1:
        await process_input(ques1, "Question 1")
    if ques2:
        await process_input(ques2, "Question 2")
    if ques3:
        await process_input(ques3, "Question 3")

# Button
if st.button("🚀 Run Guardrails", disabled=not (ques1 or ques2 or ques3)):
    asyncio.run(run_all_inputs())

        

