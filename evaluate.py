"""
evaluate.py

Compara los puntajes del sistema con los puntajes originales de los profesores
(su juicio habitual, antes de los criterios), usando los textos de la carpeta
evaluation/, que el sistema nunca ve como referencia.

Para cada texto:
- Lee los puntajes originales del profesor (línea 'Original scores:').
  Acepta rangos como '2.5 or 3'.
- Genera la evaluación del sistema.
- Muestra la diferencia en cada criterio.
- Guarda la evaluación completa del sistema en la carpeta results/.
"""

from pathlib import Path

from retrieval import read_file, get_field
from checks import get_section
from pipeline import assess_text

EVALUATION_DIR = Path(__file__).parent / "evaluation"
RESULTS_DIR = Path(__file__).parent / "results"
CRITERIA = ["Content", "Organization", "Language"]


def parse_original_scores(line):
    """
    Convierte 'Content 3 | Organization 4 | Language 2.5 or 3' en un diccionario
    con rangos: {'Content': (3.0, 3.0), 'Organization': (4.0, 4.0), 'Language': (2.5, 3.0)}.
    Un puntaje único se guarda como un rango donde el mínimo y el máximo son iguales.
    """
    scores = {}
    for part in line.split("|"):
        words = part.split()
        name = words[0]
        values = []
        for word in words[1:]:
            if word != "or":
                values.append(float(word.replace(",", ".")))
        scores[name] = (min(values), max(values))
    return scores


def distance(system_score, teacher_range):
    """
    Diferencia entre el puntaje del sistema y el rango del profesor.
    Es 0 si el puntaje del sistema está dentro del rango.
    Es negativa si el sistema puso menos, y positiva si puso más.
    """
    low, high = teacher_range
    if system_score < low:
        return system_score - low
    if system_score > high:
        return system_score - high
    return 0.0


def format_range(teacher_range):
    """Muestra (3.0, 3.0) como '3.0' y (2.5, 3.0) como '2.5-3.0'."""
    low, high = teacher_range
    if low == high:
        return str(low)
    return f"{low}-{high}"


def load_evaluation_sample(path):
    """Lee un archivo de evaluación y devuelve sus datos."""
    text = read_file(path)
    return {
        "name": path.stem,
        "task": get_field(text, "Task"),
        "teacher_scores": parse_original_scores(get_field(text, "Original scores")),
        "student_text": "\n".join(get_section(text, "Text")).strip(),
    }


def evaluate():
    RESULTS_DIR.mkdir(exist_ok=True)
    differences = []   # todas las diferencias, para el resumen final

    for path in sorted(EVALUATION_DIR.glob("*.md")):
        sample = load_evaluation_sample(path)

        print(f"\n=== {sample['name']} ===")
        print("Evaluando...")
        try:
            result = assess_text(sample["student_text"], sample["task"])
        except ValueError as error:
            print(f"No se pudo evaluar este texto: {error}")
            continue

        # Guarda la evaluación completa para revisar las justificaciones después
        (RESULTS_DIR / f"{sample['name']}.md").write_text(result["assessment"], encoding="utf-8")

        system_scores = result["scores"]
        if system_scores is None:
            print("El sistema no entregó una línea 'Scores:' válida. Revisa results/.")
            continue

        print(f"{'Criterio':<14}{'Profesor':>10}{'Sistema':>10}{'Diferencia':>12}")
        for criterion in CRITERIA:
            teacher = sample["teacher_scores"][criterion]
            system = system_scores[criterion]
            difference = distance(system, teacher)
            differences.append(abs(difference))
            print(f"{criterion:<14}{format_range(teacher):>10}{system:>10}{difference:>+12}")

    # ---------- Resumen ----------
    if differences:
        exact = 0
        close = 0
        for difference in differences:
            if difference == 0:
                exact += 1
            if difference <= 0.5:
                close += 1
        total = len(differences)

        print("\n=== RESUMEN ===")
        print(f"Puntajes comparados: {total}")
        print(f"Coinciden (o están dentro del rango del profesor): {exact} ({exact / total:.0%})")
        print(f"Diferencia de 0.5 o menos: {close} ({close / total:.0%})")
        print(f"Diferencia promedio: {sum(differences) / total:.2f}")
        print("\nLas evaluaciones completas del sistema están en la carpeta results/.")


if __name__ == "__main__":
    evaluate()