# Control Protocol Specification

## Types
| Name       | Type          | Size in Bytes |
| ---------- | ------------- | ------------- |
| fID        | char          | 1             |
| vec\<char> | char + char[] | 1 + X      |
|            |               |               |

## PY -> ESP
| *char* fID | fName                                                                     |
| ---------- | ------------------------------------------------------------------------- |
| 0          | startRecipe(vec\<char> recipe_name)                                       |
| 1          | doStep(double stable_offset, double delta_target, vec\<char> instruction) |
| 2          | finishRecipe()                                                            |
| 3          | abortRecipe()                                                             |
|            |                                                                           |

## ESP -> PY
| *char* fID | fName                       |
| ---------- | --------------------------- |
| 0          | notifyWeight(double weight) |
|            |                             |
