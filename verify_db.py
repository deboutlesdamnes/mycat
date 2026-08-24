# -*- coding: utf-8 -*-
import sqlite3
db = sqlite3.connect(r"c:\Users\jason\Documents\mycat\mycat_knowledge.db")
c = db.cursor()
out = []

out.append("=== knowledge_points by subject ===")
for r in c.execute("SELECT subject, COUNT(*) FROM knowledge_points GROUP BY subject ORDER BY 2 DESC"):
    out.append(f"{r[0]}: {r[1]}")

out.append("\n=== question_types ===")
for r in c.execute("SELECT category, name, frequency FROM question_types ORDER BY id"):
    out.append(f"[{r[0]}] {r[1]}  {r[2] or ''}")

out.append("\n=== mcat_sections ===")
for r in c.execute("SELECT name, total_questions, passages, passage_based, discrete FROM mcat_sections"):
    out.append(r)

out.append("\n=== sources ===")
for r in c.execute("SELECT filename, publisher, subject FROM sources"):
    out.append(r)

open(r"c:\Users\jason\Documents\mycat\verify_out.txt", "w", encoding="utf-8").write("\n".join(str(x) for x in out))
print("done")
