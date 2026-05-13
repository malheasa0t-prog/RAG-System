"""Simple command-line chat for local testing."""

import uuid

try:
    from .rag_core import answer_question
except ImportError:
    from rag_core import answer_question


def main():
    session_id = str(uuid.uuid4())
    history = []
    print("مساعد Serva-S جاهز. اكتب exit للخروج.")

    while True:
        question = input("You: ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue

        answer, session_id = answer_question(question, history, session_id, save=False)
        history.extend([
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ])
        print(f"\nAI: {answer}\n")


if __name__ == "__main__":
    main()
