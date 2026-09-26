"""
pipeline.py

Une todas las piezas del sistema:

1. checks.py     -> hechos objetivos (conteo de palabras, vocabulario enseñado)
2. retrieval.py  -> contexto (rúbrica, criterios, task sheet, muestras de referencia)
3. prompts.py    -> prompts para el LLM
4. LLM           -> evaluación para el profesor y retroalimentación para el estudiante
"""

from config import client, MODELO
from retrieval import retrieve_context, load_task
from checks import run_checks
from prompts import (
    TEACHER_SYSTEM_PROMPT,
    STUDENT_SYSTEM_PROMPT,
    build_teacher_prompt,
    build_student_prompt,
)


def call_llm(system_prompt, user_prompt, temperature, max_tokens):
    """Llama al LLM con un mensaje de sistema y uno de usuario, y devuelve el texto de la respuesta."""
    response = client.chat.completions.create(
        model=MODELO,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        extra_body={"reasoning": {"effort": "low"}},
    )
    content = response.choices[0].message.content
    finish_reason = response.choices[0].finish_reason

    # Algunos modelos gratuitos a veces devuelven una respuesta vacía
    if not content:
        raise ValueError(f"El modelo devolvió una respuesta vacía (finish_reason: {finish_reason}). "
            "Intenta de nuevo o cambia de modelo.")
    
     # "length" significa que el modelo se quedó sin tokens y la respuesta quedó cortada
    if finish_reason == "length":
        raise ValueError("La respuesta quedó cortada por falta de tokens. Aumenta max_tokens.")
    return content


def parse_scores(assessment):
    """
    Busca la línea 'Scores: Content 3 | Organization 2.5 | Language 3'
    y devuelve un diccionario: {'Content': 3.0, 'Organization': 2.5, 'Language': 3.0}.
    Devuelve None si no encuentra la línea.
    """
    for line in assessment.splitlines():
        # Quita asteriscos por si el modelo usó negrita (**Scores:**)
        clean = line.replace("*", "").strip()
        if clean.startswith("Scores:"):
            scores = {}
            parts = clean.split(":", 1)[1].split("|")
            for part in parts:
                name, value = part.split()
                scores[name] = float(value.replace(",", "."))
            return scores
    return None


def assess_text(text, task_id):
    """Genera la evaluación para el profesor."""
    checks = run_checks(text, task_id)
    context = retrieve_context(task_id)
    user_prompt = build_teacher_prompt(text, context, checks)

    # Temperatura baja: queremos puntajes consistentes, no creatividad
    assessment = call_llm(TEACHER_SYSTEM_PROMPT, user_prompt, temperature=0.2, max_tokens=12000)

    return {
        "checks": checks,
        "assessment": assessment,
        "scores": parse_scores(assessment),
    }


def student_feedback(text, assessment, task_id):
    """Genera la retroalimentación para el estudiante, a partir de la evaluación del profesor."""
    task_text = load_task(task_id)
    user_prompt = build_student_prompt(text, assessment, task_text)

    # Temperatura un poco más alta: un tono más natural y cercano
    return call_llm(STUDENT_SYSTEM_PROMPT, user_prompt, temperature=0.5, max_tokens=6000)


# Prueba rápida: ejecuta "python pipeline.py" en la terminal
if __name__ == "__main__":
    test_text = (
        "get up at 5:45 A.M. a take shower, get dressed, after that form up in "
        "the alpatacal cordid and go to the mess hall where the cadet have a "
        "breakfast. After I go to classroom where have classes at 8.00. Then, "
        "form up at 1.00 for mess hall to have lunch with the company. Then do "
        "sports or classes from 15.00 to 18.00. In the night, go to barracks "
        "and sleep."
    )

    print("Evaluando el texto...\n")
    result = assess_text(test_text, "cadet_routine")

    print("=== EVALUACIÓN PARA EL PROFESOR ===")
    print(result["assessment"])
    print("\nPuntajes leídos por el código:", result["scores"])

    print("\nGenerando retroalimentación para el estudiante...\n")
    print("=== RETROALIMENTACIÓN PARA EL ESTUDIANTE ===")
    print(student_feedback(test_text, result["assessment"], "cadet_routine"))