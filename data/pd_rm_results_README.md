# PD and RM per-file results

`pd_rm_results.csv` contains the recorded screening flags for the 234 historical PDF inputs, before study-level deduplication. Each row represents an input file, not a unique study. This table contains PD and RM workflow results and the recorded ground-truth study names, not independent comparator results or complete raw AI responses.

| Column | Meaning |
| --- | --- |
| `Covidence_ID` | Recorded Covidence identifier, retained without remapping. Not necessarily a unique file identifier. |
| `Historical_PDF_filename` | Historical PDF filename, retained without renaming. |
| `PD_initial_verification_flag` | Stored binary verification result for the initial generated definition/summary. |
| `PD_rechecked_verification_flag` | Stored binary verification result for the rechecked generated definition/summary. |
| `PD_candidate_flag` | Stored final PD screening flag. |
| `RM_keyword_flag_k_d` | k(d): the historical case-insensitive RAAC string-search result within the RM workflow. |
| `RM_AI_cleaned_flag_r_d` | r(d): the cleaned AI response flag recorded in the source summary. |
| `RM_category_k_r` | Ordered pair k(d), r(d): Y_Y, Y_N, N_Y or N_N. |
| `RM_candidate_flag_k_OR_r` | Y when either k(d) or r(d) is Y; otherwise N. |
| `Ground_truth_study` | Ground-truth study name recorded in the source summary. Blank entries are preserved. |

Y and N retain the recorded binary outcomes. Screening flags are not expert relevance judgments. PD verification concerns generated outputs rather than direct verification against the source PDF.

The file-level RM categories comprise 4 Y_Y, 8 Y_N, 10 N_Y and 212 N_N inputs. These are not deduplicated study-level performance counts.

The table was reorganized on 5 November 2026 without changing row order, identifiers, screening values or ground-truth study names. Local folder names and internal notes are omitted. No AI calls, remapping or deduplication were performed during reorganization. Column names differ from the earlier internal summary; scripts expecting that earlier schema require the original internal file.
