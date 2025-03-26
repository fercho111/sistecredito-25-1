# Documento de Arquitectura y Metodología  
*Equipo Hackathon SISTECREDITO - EIA 2025*  
Marzo 2025

---

## 1. Introducción

Este documento describe la arquitectura, metodología y decisiones técnicas adoptadas en el desarrollo de un asistente virtual para negociación de compromisos de pago, basado en inteligencia artificial y la arquitectura *RAG* (Retrieval-Augmented Generation).

---

## 2. Arquitectura General de la Solución

El sistema propuesto sigue una arquitectura modular, basada en cinco etapas principales:

1.⁠ ⁠*Entrada del Cliente o Agente:*  
   El cliente se comunica a través de una interfaz (chatbot o API), enviando su solicitud.

2.⁠ ⁠*Conversión a Embeddings y Recuperación:*
   - El texto del cliente se transforma en un vector semántico (embedding).
   - Se realiza una búsqueda vectorial en una base de datos (ChromaDB) para recuperar casos históricos y plantillas relevantes.

3.⁠ ⁠*Procesamiento con LLM (modelo generativo):*
   - El modelo (como GPT-4o o DeepSeek) recibe el mensaje original y los documentos recuperados.
   - Genera una respuesta negociada contextualizada.

4.⁠ ⁠*Generación de Propuesta de Compromiso de Pago:*
   - La respuesta generada incorpora lenguaje y formato de las plantillas oficiales.
   - Se adapta según el tipo de dificultad reportada por el cliente.

5.⁠ ⁠*Exposición vía API (FastAPI):*
   - La respuesta final es devuelta mediante un endpoint REST.
   - El sistema puede integrarse con otras plataformas (CRM, WhatsApp, etc.).

---

## 3. Integración de la Base de Conocimiento

La base de conocimiento está compuesta por:

•⁠  ⁠*Casos históricos:* Transcripciones y registros de negociaciones previas.
•⁠  ⁠*Estrategias etiquetadas:* Asociación de casos con estrategias efectivas aplicadas.

Cada documento se preprocesa, tokeniza y se le genera un embedding. Estos se almacenan en un motor vectorial para realizar búsqueda semántica.  
Cuando un cliente interactúa, se recuperan los fragmentos más relevantes y se incluyen en el prompt del modelo generativo.

---

## 4. Adaptación Dinámica de Propuestas

Gracias a la arquitectura RAG, el sistema genera respuestas personalizadas mediante:

•⁠  ⁠*Comprensión del contexto del cliente:* Analiza texto y extrae intención.
•⁠  ⁠*Sugerencia de estrategia:* Basado en similitud con casos anteriores.
•⁠  ⁠*Redacción automatizada:* Usa el LLM para generar propuestas formales, empáticas y alineadas con las políticas de la empresa.

