#import "/commands.typ": *

// woodcore:object heading title
== Required reliability and consequence class
// woodcore:/object title

// woodcore:object text p1
The required reliability may be differentiated depending on the limit state and reference period, for the whole structure or for individual members (SIA 260, 2.3.4). It may depend on the type and consequences of failure, the amount of acceptable damage, the importance of the building in dealing with a catastrophe, the expenditure to reduce the risk and the possibilities of monitoring and maintenance (2.3.5). [Justify the choice.]
// woodcore:/object p1

// woodcore:object doc-choice consequence-class
#doc-choice(
  label: [Consequence class of a failure (to be agreed)],
  options: (
    (id: "cc1", label: [CC1: low consequences (loss of human life, economic, social or environmental consequences low or negligible)]),
    (id: "cc2", label: [CC2: medium consequences (loss of human life, considerable economic, social or environmental consequences)]),
    (id: "cc3", label: [CC3: high consequences (loss of human life, very great economic, social or environmental consequences)]),
  ),
  selected: "cc2",
)
// woodcore:/object consequence-class
