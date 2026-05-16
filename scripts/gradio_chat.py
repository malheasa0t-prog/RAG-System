"""Small Gradio UI wrapper around rag_core.py."""

import uuid

import gradio as gr

try:
    from .app_config import GRADIO_SERVER_NAME, GRADIO_SERVER_PORT, GRADIO_SHARE
    from .rag_core import answer_question
except ImportError:
    from app_config import GRADIO_SERVER_NAME, GRADIO_SERVER_PORT, GRADIO_SHARE
    from rag_core import answer_question


def create_interface():
    with gr.Blocks(title="مساعد المتجر الذكي") as demo:
        gr.Markdown(
            """
            # مساعد المتجر الذكي
            اسألني عن الخدمات، الأسعار، طريقة الطلب، أو سياسات المتجر.
            """
        )

        chatbot = gr.Chatbot(label="المحادثة", height=500)
        message_box = gr.Textbox(
            label="رسالتك",
            placeholder="مثال: هل خدمة CapCut متوفرة؟",
            rtl=True,
        )
        session_state = gr.State(value=str(uuid.uuid4()))
        clear_button = gr.Button("مسح المحادثة")

        def on_submit(user_message, history, session_id):
            history = history or []
            if not str(user_message or "").strip():
                return "", history, session_id

            answer, session_id = answer_question(
                user_message,
                history,
                session_id,
                save=True,
                rate_limit_key=session_id,
            )
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": answer})
            return "", history, session_id

        message_box.submit(
            on_submit,
            [message_box, chatbot, session_state],
            [message_box, chatbot, session_state],
        )
        clear_button.click(lambda: ([], str(uuid.uuid4())), None, [chatbot, session_state])

    return demo


if __name__ == "__main__":
    app = create_interface()
    app.launch(
        share=GRADIO_SHARE,
        server_name=GRADIO_SERVER_NAME,
        server_port=GRADIO_SERVER_PORT,
    )
