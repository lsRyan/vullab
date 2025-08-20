# Requirements for Tests and Experiments

VulLab is a resource intensive tool It requires considerable computational power to execute all its modules in a large quantity of smart contracts. Even with all of the techniques employed to try to increase efficiency, such asa multi-threading, execution times are still considerable when using datasets with more than a few dozens entries.

The smoke test and reduced experiment presented in the project's README was specially designed to be lightweight enough to enable its execution in a modest environment in a reasonable amount of time. As a quick reference, this document provides a table with several hardware selections and the estimated execution time for each of them when running the tests.

We also offer te same specifications and respective estimates in the case of our [complete experiment](/docs/Complete_Experiment.md).

## Hardware Requirements


### Smoke Test
| Threads  | RAM (Gib)  | Disk Space (Gib) | Estimated Time (h) | Recommended |
|:--------:|:----------:|:----------------:|:------------------:|:-----------:|
| 4        | 4          | 40               | 6                  |             |
| 4        | 8          | 40               | 6                  |             |
| 8        | 8          | 40               | 3                  | X           |

### Reduced Experiment
| Threads  | RAM (Gib)  | Disk Space (Gib) | Estimated Time (h) | Recommended |
|:--------:|:----------:|:----------------:|:------------------:|:-----------:|
| 4        | 8          | 40               | 60                 |             |
| 8        | 8          | 40               | 30                 | X           |
| 16       | 12         | 40               | 15                 |             |

### Complete Experiment
| Threads  | RAM (Gib)  | Disk Space (Gib) | Estimated Time (h) | Recommended |
|:--------:|:----------:|:----------------:|:------------------:|:-----------:|
| 8        | 16         | 120              | ~1080  (~45days)   |             |
| 20       | 16         | 120              | ~480 (~20 days)    | X           |
| 30       | 32         | 120              | ~320 (~14 days)    |             |