[![GitHub license](https://img.shields.io/github/license/martibosch/urban-es-proposal.svg)](https://github.com/martibosch/urban-es-proposal/blob/master/LICENSE)

# Urban ES proposal

Proposal for a platform to evaluate urban ecosystem services

## Instructions

1. Create a conda environment

```
make create_environment
```

2. Activate it

```
conda activate urban-es-proposal
```

You can now generate all the data for the plots:

```
make candidate_pixels vulnerable_pop heat_mitigation
```

and compile the one-pager DOCX and PDF:

```
make one_pager_docx one_pager_pdf
```

## Acknowledgments

* Project based on [Henk Griffioen's version](https://github.com/hgrif/cookiecutter-ds-python) of the [cookiecutter data science project template](https://drivendata.github.io/cookiecutter-data-science). #cookiecutterdatascience
