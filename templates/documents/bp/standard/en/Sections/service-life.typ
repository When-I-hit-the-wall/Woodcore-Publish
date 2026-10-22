#import "/commands.typ": *

// woodcore:object heading title
== Service life
// woodcore:/object title
// woodcore:shared service-life

// woodcore:object text p1
The service life is the period during which, according to present knowledge, the building is to satisfy the uses defined in the service criteria agreement. It is agreed with the owner; during this period the owner carries out the periodic maintenance work.
// woodcore:/object p1

// woodcore:object text service-life-class
*Service life of the structure (indicative values, SIA 260, 2.3.2)*: Building or other construction works of average importance: 50 years
// woodcore:/object service-life-class

// woodcore:object table service-life-table
#figure(
  table(
    columns: (auto, auto),
    align: (left, left),
    table.hline(stroke: 1pt),
    table.header([*Member*], [*Service life*]),  // woodcore:hidden 3=[Remark]
    table.hline(stroke: 0.5pt),
    [Structure], [50 years],  // woodcore:hidden 3=[]
    [Waterproofing], [25 years],  // woodcore:hidden 3=[]
    [Facade], [25 years],  // woodcore:hidden 3=[]
    [Roof covering], [25 years],  // woodcore:hidden 3=[]
    [Replaceable members], [25 years],  // woodcore:hidden 3=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Agreed service life by member],
)
// woodcore:/object service-life-table
// woodcore:/shared service-life
