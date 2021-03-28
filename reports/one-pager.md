---
keywords: Urban ecosystem services
geometry: "top=1.5cm, bottom=1.5cm, left=1.5cm, right=1.5cm"
header-includes: 
    - \pagenumbering{gobble}
    - \usepackage{fontawesome}
    - \usepackage{titlesec}
    - \titlespacing*{\subsection}{0pt}{.75em}{-.25em}
    - \titlespacing*{\paragraph}{0pt}{.5em}{.5em}
...

# A cloud platform to assess urban ecosystem services

#### Urban ecosystem services

Nature-based contributions to urban design are central to climate change adaptation, mitigation and disaster risk reduction. Urban green infrastructure provides notable benefits to the rapidly growing urban populations. Examples of such benefits - often referred to as urban ecosystem services- include the alleviation of urban heat islands, flood risk mitigation, pollution removal or the provision of recreational opportunities [1, 2].

#### Spatial planning tools

Geographic information systems (GIS) hold strong potential to inform and support spatial planning. Notable examples include geodata portals such as [ASIT (Vaud)](https://www.asitvd.ch/) or [SITG (Geneva)](https://ge.ch/sitg/), interactive visualization platforms such as [NatCap Viz](http://viz.naturalcapitalproject.stanford.edu/) or collaborative networks such as [Metabolism of Cities](https://metabolismofcities.org/).

## Objective

We propose to prototype and implement a cloud-based platform to experiment with models of urban ecosystem services, as well as to access, share and display datasets and results, allowing city-planners and decision-makers to experiment with scenarios of spatial development and the associated environmental impacts. This platform would include state-of-the-art ecosystem services models, and the latest available datasets of Swiss urban areas. 

## Example case: mapping potential urban heat mitigation to protect vulnerable dwellers

The number of tropical nights (with T$_{min}$ < 20°C) in Swiss urban areas has increased dramatically in recent decades [3]. Urban green infrastructure, especially trees, can help reduce urban temperatures by modifying thermal properties of the urban fabric and providing shade and evapotranspirative cooling. By combining the InVEST urban cooling model [4] with population data from the Swiss Federal Statistical Office [5], greening scenarios can be designed to protect the most vulnerable urban dwellers (aged 60+), as illustrated in Figure 1.

![Nighttime (9 p.m.) T in Lausanne in 24/7/2019 (left) [6], potential heat mitigation by planting 35000 trees to protect vulnerable dwellers (center), and comparison of the number of vulnerable dwellers exposed to nighttime temperatures over 25°C when randomly planting trees and planting them to protect the vulnerable dwellers (right) [7].](reports/figures/figure.png)

## Target audience

The demand for the platform is motivated by the lack of effective tools to integrate urban ecosystem services in spatial planning. The platform is designed for:

* **GIS engineers**: apply the models of ecosystem services to evaluate the environmental impacts of master plans, future urbanization scenarios and to assess the effects of specific interventions
* **Planners and decision-makers**: visualize and analyze the results to support urban planning, compare alternative scenarios and spatially prioritize interventions

## Functionalities

The platform would build on the start-of-the-art tools for data science and scientific computing to provide an efficient cloud-based experimentation with advanced models of ecosystem services in Swiss urban areas:

* **Data curation** of datasets from administrative sources in Switzerland (SWISSTOPO, Swiss Federal Statistics Geodata, MeteoSwiss, ASIT...)
* A **user-friendly interface** to cutting-edge models of urban ecosystem services (urban heat island mitigation, flood risk mitigation, recreation opportunities, carbon sequestration...)
* **Interactive visualizations** of the spatial provision of ecosystem services with multiple layers and side-by-side comparison of alternative scenarios.

## References

1. Gómez-Baggethun, Erik, et al. "Urban ecosystem services" Urbanization, biodiversity and ecosystem services: Challenges and opportunities. Springer, Dordrecht, 2013. 175-251.
2. Bolund, Per, and Sven Hunhammar. "Ecosystem services in urban areas." Ecological economics 29.2 (1999): 293-301.
3. Burgstall, Annkatrin, et al. Representing the urban heat island effect in future climates. Scientific Report MeteoSwiss No. 105, 2019.
4. Sharp, R., et al. "InVEST 3.8.0 User's guide." The Natural Capital Project (2020).
5. Bosch, Martí. "swisslandstats-geopy: Python tools for the land statistics datasets from the Swiss Federal Statistical Office." Journal of Open Source Software 4.41 (2019): 1511.
6. Bosch, Martí, et al. "A spatially-explicit approach to simulate urban heat islands in complex urban landscapes." Geoscientific Model Development Discussions (2020): 1-22.
7. Bosch, Martí, et al. "Evaluating urban greening scenarios for urban heat mitigation: a spatially-explicit approach." bioRxiv (2020).

##### Contact:

Martí Bosch - Urban and Regional Planning Community (CEAT), EPFL - \href{mailto:marti.bosch@epfl.ch}{$\;$ \faEnvelope $\,$ marti.bosch@epfl.ch}
