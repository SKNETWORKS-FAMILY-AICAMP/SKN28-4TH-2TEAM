from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.rag_pipeline import RagPipeline

pipeline = RagPipeline()

questions = [
    "AI컴퓨팅학과 합격 여부 알려줘",
    "내 GPA 3.8인데 AI컴퓨팅학과 붙을 수 있어?",
    "AI컴퓨팅학과 합격자 발표 일정 알려줘",
    "AI컴퓨팅학과 석사 지원 자격은?",
]

for question in questions:
    result = pipeline.run(question)

    print("=" * 80)
    print("Q:", question)
    print("A:", result.answer)
    print("route:", result.route)
    print("intent:", result.intent)
    print("warnings:", result.warnings)
