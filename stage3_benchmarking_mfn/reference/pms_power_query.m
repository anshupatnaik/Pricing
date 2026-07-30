section Section1;

shared moves_simulator = let
    // Retrieve parameters from Excel
    Params = Excel.CurrentWorkbook(){[Name="Terminalname"]}[Content],
    DateFromParams = Excel.CurrentWorkbook(){[Name="From_Date"]}[Content],
    DateToParams = Excel.CurrentWorkbook(){[Name="To_Date"]}[Content],
    Params2 = Excel.CurrentWorkbook(){[Name="Operator1"]}[Content],
    Params4 = Excel.CurrentWorkbook(){[Name="Operator2"]}[Content],
    Params5 = Excel.CurrentWorkbook(){[Name="Operator3"]}[Content],
    Params6 = Excel.CurrentWorkbook(){[Name="Operator4"]}[Content],
    Params7 = Excel.CurrentWorkbook(){[Name="Operator5"]}[Content],
    Params8 = Excel.CurrentWorkbook(){[Name="Operator6"]}[Content],
    Params9 = Excel.CurrentWorkbook(){[Name="Service1"]}[Content],  
    Params10 = Excel.CurrentWorkbook(){[Name="Service2"]}[Content],
    Params11 = Excel.CurrentWorkbook(){[Name="Service3"]}[Content],
    Params12 = Excel.CurrentWorkbook(){[Name="Service4"]}[Content],
    Params13 = Excel.CurrentWorkbook(){[Name="Service5"]}[Content],
    Params14 = Excel.CurrentWorkbook(){[Name="Service6"]}[Content],
    Params15 = Excel.CurrentWorkbook(){[Name="Service7"]}[Content],
    Params16 = Excel.CurrentWorkbook(){[Name="Service8"]}[Content],
    Params17 = Excel.CurrentWorkbook(){[Name="Service9"]}[Content],
    Params18 = Excel.CurrentWorkbook(){[Name="Service10"]}[Content],
    Params19 = Excel.CurrentWorkbook(){[Name="Service11"]}[Content],
    Params20 = Excel.CurrentWorkbook(){[Name="Service12"]}[Content],
    Params21 = Excel.CurrentWorkbook(){[Name="Service13"]}[Content],
    Params22 = Excel.CurrentWorkbook(){[Name="Service14"]}[Content],
    Params23 = Excel.CurrentWorkbook(){[Name="Service15"]}[Content],
    Params24 = Excel.CurrentWorkbook(){[Name="Operator7"]}[Content],
    Params25 = Excel.CurrentWorkbook(){[Name="Operator8"]}[Content],
    Params26 = Excel.CurrentWorkbook(){[Name="Operator9"]}[Content],
    Params27 = Excel.CurrentWorkbook(){[Name="Operator10"]}[Content],
    Params28 = Excel.CurrentWorkbook(){[Name="Operator11"]}[Content],
    Params29 = Excel.CurrentWorkbook(){[Name="Operator12"]}[Content],
    Params30 = Excel.CurrentWorkbook(){[Name="Operator13"]}[Content],
    Params31 = Excel.CurrentWorkbook(){[Name="Operator14"]}[Content],
    Params32 = Excel.CurrentWorkbook(){[Name="Operator15"]}[Content],

    // Convert parameters to appropriate types
    #"Changed Type_Terminal" = Table.TransformColumnTypes(Params,{{"Column1", type text}}),
    #"Changed Cont_Operator_Type" = Table.TransformColumnTypes(Params2,{{"Column1", type text}}),
    #"Changed FromDate Type" = Table.TransformColumnTypes(DateFromParams,{{"Column1", type date}}),
    #"Changed ToDate Type" = Table.TransformColumnTypes(DateToParams,{{"Column1", type date}}),
    #"Changed Cont_Operator2_Type" = Table.TransformColumnTypes(Params4,{{"Column1", type text}}),
    #"Changed Cont_Operator3_Type" = Table.TransformColumnTypes(Params5,{{"Column1", type text}}),
    #"Changed Cont_Operator4_Type" = Table.TransformColumnTypes(Params6,{{"Column1", type text}}),
    #"Changed Cont_Operator5_Type" = Table.TransformColumnTypes(Params7,{{"Column1", type text}}),
    #"Changed Cont_Operator6_Type" = Table.TransformColumnTypes(Params8,{{"Column1", type text}}),
    #"Changed Cont_service_Type" = Table.TransformColumnTypes(Params9,{{"Column1", type text}}),
    #"Changed Cont_service2_Type" = Table.TransformColumnTypes(Params10,{{"Column1", type text}}),
    #"Changed Cont_service3_Type" = Table.TransformColumnTypes(Params11,{{"Column1", type text}}),
    #"Changed Cont_service4_Type" = Table.TransformColumnTypes(Params12,{{"Column1", type text}}),
    #"Changed Cont_service5_Type" = Table.TransformColumnTypes(Params13,{{"Column1", type text}}),
    #"Changed Cont_service6_Type" = Table.TransformColumnTypes(Params14,{{"Column1", type text}}),
    #"Changed Cont_service7_Type" = Table.TransformColumnTypes(Params15,{{"Column1", type text}}),
    #"Changed Cont_service8_Type" = Table.TransformColumnTypes(Params16,{{"Column1", type text}}),
    #"Changed Cont_service9_Type" = Table.TransformColumnTypes(Params17,{{"Column1", type text}}),
    #"Changed Cont_service10_Type" = Table.TransformColumnTypes(Params18,{{"Column1", type text}}),
    #"Changed Cont_service11_Type" = Table.TransformColumnTypes(Params19,{{"Column1", type text}}),
    #"Changed Cont_service12_Type" = Table.TransformColumnTypes(Params20,{{"Column1", type text}}),
    #"Changed Cont_service13_Type" = Table.TransformColumnTypes(Params21,{{"Column1", type text}}),
    #"Changed Cont_service14_Type" = Table.TransformColumnTypes(Params22,{{"Column1", type text}}),
    #"Changed Cont_service15_Type" = Table.TransformColumnTypes(Params23,{{"Column1", type text}}),
    #"Changed Cont_Operator7_Type" = Table.TransformColumnTypes(Params24,{{"Column1", type text}}),
    #"Changed Cont_Operator8_Type" = Table.TransformColumnTypes(Params25,{{"Column1", type text}}),
    #"Changed Cont_Operator9_Type" = Table.TransformColumnTypes(Params26,{{"Column1", type text}}),
    #"Changed Cont_Operator10_Type" = Table.TransformColumnTypes(Params27,{{"Column1", type text}}),
    #"Changed Cont_Operator11_Type" = Table.TransformColumnTypes(Params28,{{"Column1", type text}}),
    #"Changed Cont_Operator12_Type" = Table.TransformColumnTypes(Params29,{{"Column1", type text}}),
    #"Changed Cont_Operator13_Type" = Table.TransformColumnTypes(Params30,{{"Column1", type text}}),
    #"Changed Cont_Operator14_Type" = Table.TransformColumnTypes(Params31,{{"Column1", type text}}),
    #"Changed Cont_Operator15_Type" = Table.TransformColumnTypes(Params32,{{"Column1", type text}}),

    // Extract parameter values
    terminal = #"Changed Type_Terminal"{0}[Column1],
    DateFrom = Date.ToText(#"Changed FromDate Type"{0}[Column1], "yyyy-MM-dd"),
    DateTo = Date.ToText(#"Changed ToDate Type"{0}[Column1], "yyyy-MM-dd"),
    operator = #"Changed Cont_Operator_Type"{0}[Column1],
    operator2 = #"Changed Cont_Operator2_Type"{0}[Column1],
    operator3 = #"Changed Cont_Operator3_Type"{0}[Column1],
    operator4 = #"Changed Cont_Operator4_Type"{0}[Column1],
    operator5 = #"Changed Cont_Operator5_Type"{0}[Column1],
    operator6 = #"Changed Cont_Operator6_Type"{0}[Column1],
    service = #"Changed Cont_service_Type"{0}[Column1],
    service2 = #"Changed Cont_service2_Type"{0}[Column1],
    service3 = #"Changed Cont_service3_Type"{0}[Column1],
    service4 = #"Changed Cont_service4_Type"{0}[Column1],
    service5 = #"Changed Cont_service5_Type"{0}[Column1],
    service6 = #"Changed Cont_service6_Type"{0}[Column1],
    service7 = #"Changed Cont_service7_Type"{0}[Column1],
    service8 = #"Changed Cont_service8_Type"{0}[Column1],
    service9 = #"Changed Cont_service9_Type"{0}[Column1],
    service10 = #"Changed Cont_service10_Type"{0}[Column1],
    service11 = #"Changed Cont_service11_Type"{0}[Column1],
    service12 = #"Changed Cont_service12_Type"{0}[Column1],
    service13 = #"Changed Cont_service13_Type"{0}[Column1],
    service14 = #"Changed Cont_service14_Type"{0}[Column1],
    service15 = #"Changed Cont_service15_Type"{0}[Column1],
    operator7 = #"Changed Cont_Operator7_Type"{0}[Column1],
    operator8 = #"Changed Cont_Operator8_Type"{0}[Column1],
    operator9 = #"Changed Cont_Operator9_Type"{0}[Column1],
    operator10 = #"Changed Cont_Operator10_Type"{0}[Column1],
    operator11 = #"Changed Cont_Operator11_Type"{0}[Column1],
    operator12 = #"Changed Cont_Operator12_Type"{0}[Column1],
    operator13= #"Changed Cont_Operator13_Type"{0}[Column1],
    operator14 = #"Changed Cont_Operator14_Type"{0}[Column1],
    operator15 = #"Changed Cont_Operator15_Type"{0}[Column1],


   // Build the dynamic list of operators (only non-empty operators)
    OperatorList = List.Select({operator, operator2, operator3, operator4, operator5, operator6, operator7 , operator8, operator9, operator10, operator11, operator12, operator13, operator14, operator15}, each _ <> "" and _ <> null),

    // Build the dynamic list of services
    ServiceList = List.Select({service, service2, service3, service4, service5, service6, service7, service8, service9, service10, service11, service12, service13, service14, service15}, each _ <> "" and _ <> null),

    OperatorFilter = if List.Count(OperatorList) > 0 then "and unit_container_operator_id IN ('" & Text.Combine(OperatorList, "', '") & "') " else "",
    ServiceFilter = if List.Count(ServiceList) > 0 then "and service_name IN ('" & Text.Combine(ServiceList, "', '") & "') " else "",

    // Construct and execute the SQL query  and container_operator = '" & operator & "' " & unitrequirespowerFilter
    Source = Odbc.Query("dsn=Apache Arrow Flight SQL", 
        "select * from ""APMT-BEATS"".""Global"".""insights_and_visualizations"".""Vessel Moves Insights - Power BI"".""GBL_moves_simulator"" 
        where terminalname = '" & terminal & "' 
        and event_date >= '" & DateFrom & "' 
        and event_date <= '" & DateTo & "' 
        and event_year > 2017
        " & OperatorFilter & ServiceFilter
        ),
    #"Filtered Rows" = Table.SelectRows(Source, each true)
in
    #"Filtered Rows";

shared #"Service List" = let
    // Retrieve parameters from Excel
    Params = Excel.CurrentWorkbook(){[Name="Terminalname"]}[Content],
    DateFromParams = Excel.CurrentWorkbook(){[Name="From_Date"]}[Content],
    DateToParams = Excel.CurrentWorkbook(){[Name="To_Date"]}[Content],
    Params2 = Excel.CurrentWorkbook(){[Name="Operator1"]}[Content],
    Params4 = Excel.CurrentWorkbook(){[Name="Operator2"]}[Content],
    Params5 = Excel.CurrentWorkbook(){[Name="Operator3"]}[Content],
    Params6 = Excel.CurrentWorkbook(){[Name="Operator4"]}[Content],
    Params7 = Excel.CurrentWorkbook(){[Name="Operator5"]}[Content],
    Params8 = Excel.CurrentWorkbook(){[Name="Operator6"]}[Content],
    Params9 = Excel.CurrentWorkbook(){[Name="Service1"]}[Content],  
    Params10 = Excel.CurrentWorkbook(){[Name="Service2"]}[Content],
    Params11 = Excel.CurrentWorkbook(){[Name="Service3"]}[Content],
    Params12 = Excel.CurrentWorkbook(){[Name="Service4"]}[Content],
    Params13 = Excel.CurrentWorkbook(){[Name="Service5"]}[Content],
    Params14 = Excel.CurrentWorkbook(){[Name="Service6"]}[Content],
    Params15 = Excel.CurrentWorkbook(){[Name="Service7"]}[Content],
    Params16 = Excel.CurrentWorkbook(){[Name="Service8"]}[Content],
    Params17 = Excel.CurrentWorkbook(){[Name="Service9"]}[Content],
    Params18 = Excel.CurrentWorkbook(){[Name="Service10"]}[Content],
    Params19 = Excel.CurrentWorkbook(){[Name="Service11"]}[Content],
    Params20 = Excel.CurrentWorkbook(){[Name="Service12"]}[Content],
    Params21 = Excel.CurrentWorkbook(){[Name="Service13"]}[Content],
    Params22 = Excel.CurrentWorkbook(){[Name="Service14"]}[Content],
    Params23 = Excel.CurrentWorkbook(){[Name="Service15"]}[Content],
    Params24 = Excel.CurrentWorkbook(){[Name="Operator7"]}[Content],
    Params25 = Excel.CurrentWorkbook(){[Name="Operator8"]}[Content],
    Params26 = Excel.CurrentWorkbook(){[Name="Operator9"]}[Content],
    Params27 = Excel.CurrentWorkbook(){[Name="Operator10"]}[Content],
    Params28 = Excel.CurrentWorkbook(){[Name="Operator11"]}[Content],
    Params29 = Excel.CurrentWorkbook(){[Name="Operator12"]}[Content],
    Params30 = Excel.CurrentWorkbook(){[Name="Operator13"]}[Content],
    Params31 = Excel.CurrentWorkbook(){[Name="Operator14"]}[Content],
    Params32 = Excel.CurrentWorkbook(){[Name="Operator15"]}[Content],

    // Convert parameters to appropriate types
    #"Changed Type_Terminal" = Table.TransformColumnTypes(Params,{{"Column1", type text}}),
    #"Changed Cont_Operator_Type" = Table.TransformColumnTypes(Params2,{{"Column1", type text}}),
    #"Changed FromDate Type" = Table.TransformColumnTypes(DateFromParams,{{"Column1", type date}}),
    #"Changed ToDate Type" = Table.TransformColumnTypes(DateToParams,{{"Column1", type date}}),
    #"Changed Cont_Operator2_Type" = Table.TransformColumnTypes(Params4,{{"Column1", type text}}),
    #"Changed Cont_Operator3_Type" = Table.TransformColumnTypes(Params5,{{"Column1", type text}}),
    #"Changed Cont_Operator4_Type" = Table.TransformColumnTypes(Params6,{{"Column1", type text}}),
    #"Changed Cont_Operator5_Type" = Table.TransformColumnTypes(Params7,{{"Column1", type text}}),
    #"Changed Cont_Operator6_Type" = Table.TransformColumnTypes(Params8,{{"Column1", type text}}),
    #"Changed Cont_service_Type" = Table.TransformColumnTypes(Params9,{{"Column1", type text}}),
    #"Changed Cont_service2_Type" = Table.TransformColumnTypes(Params10,{{"Column1", type text}}),
    #"Changed Cont_service3_Type" = Table.TransformColumnTypes(Params11,{{"Column1", type text}}),
    #"Changed Cont_service4_Type" = Table.TransformColumnTypes(Params12,{{"Column1", type text}}),
    #"Changed Cont_service5_Type" = Table.TransformColumnTypes(Params13,{{"Column1", type text}}),
    #"Changed Cont_service6_Type" = Table.TransformColumnTypes(Params14,{{"Column1", type text}}),
    #"Changed Cont_service7_Type" = Table.TransformColumnTypes(Params15,{{"Column1", type text}}),
    #"Changed Cont_service8_Type" = Table.TransformColumnTypes(Params16,{{"Column1", type text}}),
    #"Changed Cont_service9_Type" = Table.TransformColumnTypes(Params17,{{"Column1", type text}}),
    #"Changed Cont_service10_Type" = Table.TransformColumnTypes(Params18,{{"Column1", type text}}),
    #"Changed Cont_service11_Type" = Table.TransformColumnTypes(Params19,{{"Column1", type text}}),
    #"Changed Cont_service12_Type" = Table.TransformColumnTypes(Params20,{{"Column1", type text}}),
    #"Changed Cont_service13_Type" = Table.TransformColumnTypes(Params21,{{"Column1", type text}}),
    #"Changed Cont_service14_Type" = Table.TransformColumnTypes(Params22,{{"Column1", type text}}),
    #"Changed Cont_service15_Type" = Table.TransformColumnTypes(Params23,{{"Column1", type text}}),
    #"Changed Cont_Operator7_Type" = Table.TransformColumnTypes(Params24,{{"Column1", type text}}),
    #"Changed Cont_Operator8_Type" = Table.TransformColumnTypes(Params25,{{"Column1", type text}}),
    #"Changed Cont_Operator9_Type" = Table.TransformColumnTypes(Params26,{{"Column1", type text}}),
    #"Changed Cont_Operator10_Type" = Table.TransformColumnTypes(Params27,{{"Column1", type text}}),
    #"Changed Cont_Operator11_Type" = Table.TransformColumnTypes(Params28,{{"Column1", type text}}),
    #"Changed Cont_Operator12_Type" = Table.TransformColumnTypes(Params29,{{"Column1", type text}}),
    #"Changed Cont_Operator13_Type" = Table.TransformColumnTypes(Params30,{{"Column1", type text}}),
    #"Changed Cont_Operator14_Type" = Table.TransformColumnTypes(Params31,{{"Column1", type text}}),
    #"Changed Cont_Operator15_Type" = Table.TransformColumnTypes(Params32,{{"Column1", type text}}),

    // Extract parameter values
    terminal = #"Changed Type_Terminal"{0}[Column1],
    DateFrom = Date.ToText(#"Changed FromDate Type"{0}[Column1], "yyyy-MM-dd"),
    DateTo = Date.ToText(#"Changed ToDate Type"{0}[Column1], "yyyy-MM-dd"),
    operator = #"Changed Cont_Operator_Type"{0}[Column1],
    operator2 = #"Changed Cont_Operator2_Type"{0}[Column1],
    operator3 = #"Changed Cont_Operator3_Type"{0}[Column1],
    operator4 = #"Changed Cont_Operator4_Type"{0}[Column1],
    operator5 = #"Changed Cont_Operator5_Type"{0}[Column1],
    operator6 = #"Changed Cont_Operator6_Type"{0}[Column1],
    service = #"Changed Cont_service_Type"{0}[Column1],
    service2 = #"Changed Cont_service2_Type"{0}[Column1],
    service3 = #"Changed Cont_service3_Type"{0}[Column1],
    service4 = #"Changed Cont_service4_Type"{0}[Column1],
    service5 = #"Changed Cont_service5_Type"{0}[Column1],
    service6 = #"Changed Cont_service6_Type"{0}[Column1],
    service7 = #"Changed Cont_service7_Type"{0}[Column1],
    service8 = #"Changed Cont_service8_Type"{0}[Column1],
    service9 = #"Changed Cont_service9_Type"{0}[Column1],
    service10 = #"Changed Cont_service10_Type"{0}[Column1],
    service11 = #"Changed Cont_service11_Type"{0}[Column1],
    service12 = #"Changed Cont_service12_Type"{0}[Column1],
    service13 = #"Changed Cont_service13_Type"{0}[Column1],
    service14 = #"Changed Cont_service14_Type"{0}[Column1],
    service15 = #"Changed Cont_service15_Type"{0}[Column1],
    operator7 = #"Changed Cont_Operator7_Type"{0}[Column1],
    operator8 = #"Changed Cont_Operator8_Type"{0}[Column1],
    operator9 = #"Changed Cont_Operator9_Type"{0}[Column1],
    operator10 = #"Changed Cont_Operator10_Type"{0}[Column1],
    operator11 = #"Changed Cont_Operator11_Type"{0}[Column1],
    operator12 = #"Changed Cont_Operator12_Type"{0}[Column1],
    operator13= #"Changed Cont_Operator13_Type"{0}[Column1],
    operator14 = #"Changed Cont_Operator14_Type"{0}[Column1],
    operator15 = #"Changed Cont_Operator15_Type"{0}[Column1],


    // Build the dynamic list of operators (only non-empty operators)
    OperatorList = List.Select({operator, operator2, operator3, operator4, operator5, operator6, operator7 , operator8, operator9, operator10, operator11, operator12, operator13, operator14, operator15}, each _ <> "" and _ <> null),

    // Build the dynamic list of services
    ServiceList = List.Select({service, service2, service3, service4, service5, service6, service7, service8, service9, service10, service11, service12, service13, service14, service15}, each _ <> "" and _ <> null),

    OperatorFilter = if List.Count(OperatorList) > 0 then "and unit_container_operator_id IN ('" & Text.Combine(OperatorList, "', '") & "') " else "",
    ServiceFilter = if List.Count(ServiceList) > 0 then "and service_name IN ('" & Text.Combine(ServiceList, "', '") & "') " else "",

    // Construct and execute the SQL query  and container_operator = '" & operator & "' " & unitrequirespowerFilter
    Source = Odbc.Query("dsn=Apache Arrow Flight SQL", 
        "select distinct terminalname, unit_container_operator_id , service_name from ""APMT-BEATS"".""Global"".""insights_and_visualizations"".""Vessel Moves Insights - Power BI"".""GBL_service_list"" 
        where terminalname = '" & terminal & "' 
        and event_date >= '" & DateFrom & "' 
        and event_date <= '" & DateTo & "' 
        " & OperatorFilter & ServiceFilter
        ),
    #"Filtered Rows" = Table.SelectRows(Source, each true)
in
    #"Filtered Rows";

shared Shiftings = let
    // Retrieve parameters from Excel
    Params = Excel.CurrentWorkbook(){[Name="Terminalname"]}[Content],
    DateFromParams = Excel.CurrentWorkbook(){[Name="From_Date"]}[Content],
    DateToParams = Excel.CurrentWorkbook(){[Name="To_Date"]}[Content],
    Params2 = Excel.CurrentWorkbook(){[Name="Operator1"]}[Content],
    Params4 = Excel.CurrentWorkbook(){[Name="Operator2"]}[Content],
    Params5 = Excel.CurrentWorkbook(){[Name="Operator3"]}[Content],
    Params6 = Excel.CurrentWorkbook(){[Name="Operator4"]}[Content],
    Params7 = Excel.CurrentWorkbook(){[Name="Operator5"]}[Content],
    Params8 = Excel.CurrentWorkbook(){[Name="Operator6"]}[Content],
    Params9 = Excel.CurrentWorkbook(){[Name="Service1"]}[Content],  
    Params10 = Excel.CurrentWorkbook(){[Name="Service2"]}[Content],
    Params11 = Excel.CurrentWorkbook(){[Name="Service3"]}[Content],
    Params12 = Excel.CurrentWorkbook(){[Name="Service4"]}[Content],
    Params13 = Excel.CurrentWorkbook(){[Name="Service5"]}[Content],
    Params14 = Excel.CurrentWorkbook(){[Name="Service6"]}[Content],
    Params15 = Excel.CurrentWorkbook(){[Name="Service7"]}[Content],
    Params16 = Excel.CurrentWorkbook(){[Name="Service8"]}[Content],
    Params17 = Excel.CurrentWorkbook(){[Name="Service9"]}[Content],
    Params18 = Excel.CurrentWorkbook(){[Name="Service10"]}[Content],
    Params19 = Excel.CurrentWorkbook(){[Name="Service11"]}[Content],
    Params20 = Excel.CurrentWorkbook(){[Name="Service12"]}[Content],
    Params21 = Excel.CurrentWorkbook(){[Name="Service13"]}[Content],
    Params22 = Excel.CurrentWorkbook(){[Name="Service14"]}[Content],
    Params23 = Excel.CurrentWorkbook(){[Name="Service15"]}[Content],
    Params24 = Excel.CurrentWorkbook(){[Name="Operator7"]}[Content],
    Params25 = Excel.CurrentWorkbook(){[Name="Operator8"]}[Content],
    Params26 = Excel.CurrentWorkbook(){[Name="Operator9"]}[Content],
    Params27 = Excel.CurrentWorkbook(){[Name="Operator10"]}[Content],
    Params28 = Excel.CurrentWorkbook(){[Name="Operator11"]}[Content],
    Params29 = Excel.CurrentWorkbook(){[Name="Operator12"]}[Content],
    Params30 = Excel.CurrentWorkbook(){[Name="Operator13"]}[Content],
    Params31 = Excel.CurrentWorkbook(){[Name="Operator14"]}[Content],
    Params32 = Excel.CurrentWorkbook(){[Name="Operator15"]}[Content],

    // Convert parameters to appropriate types
    #"Changed Type_Terminal" = Table.TransformColumnTypes(Params,{{"Column1", type text}}),
    #"Changed Cont_Operator_Type" = Table.TransformColumnTypes(Params2,{{"Column1", type text}}),
    #"Changed FromDate Type" = Table.TransformColumnTypes(DateFromParams,{{"Column1", type date}}),
    #"Changed ToDate Type" = Table.TransformColumnTypes(DateToParams,{{"Column1", type date}}),
    #"Changed Cont_Operator2_Type" = Table.TransformColumnTypes(Params4,{{"Column1", type text}}),
    #"Changed Cont_Operator3_Type" = Table.TransformColumnTypes(Params5,{{"Column1", type text}}),
    #"Changed Cont_Operator4_Type" = Table.TransformColumnTypes(Params6,{{"Column1", type text}}),
    #"Changed Cont_Operator5_Type" = Table.TransformColumnTypes(Params7,{{"Column1", type text}}),
    #"Changed Cont_Operator6_Type" = Table.TransformColumnTypes(Params8,{{"Column1", type text}}),
    #"Changed Cont_service_Type" = Table.TransformColumnTypes(Params9,{{"Column1", type text}}),
    #"Changed Cont_service2_Type" = Table.TransformColumnTypes(Params10,{{"Column1", type text}}),
    #"Changed Cont_service3_Type" = Table.TransformColumnTypes(Params11,{{"Column1", type text}}),
    #"Changed Cont_service4_Type" = Table.TransformColumnTypes(Params12,{{"Column1", type text}}),
    #"Changed Cont_service5_Type" = Table.TransformColumnTypes(Params13,{{"Column1", type text}}),
    #"Changed Cont_service6_Type" = Table.TransformColumnTypes(Params14,{{"Column1", type text}}),
    #"Changed Cont_service7_Type" = Table.TransformColumnTypes(Params15,{{"Column1", type text}}),
    #"Changed Cont_service8_Type" = Table.TransformColumnTypes(Params16,{{"Column1", type text}}),
    #"Changed Cont_service9_Type" = Table.TransformColumnTypes(Params17,{{"Column1", type text}}),
    #"Changed Cont_service10_Type" = Table.TransformColumnTypes(Params18,{{"Column1", type text}}),
    #"Changed Cont_service11_Type" = Table.TransformColumnTypes(Params19,{{"Column1", type text}}),
    #"Changed Cont_service12_Type" = Table.TransformColumnTypes(Params20,{{"Column1", type text}}),
    #"Changed Cont_service13_Type" = Table.TransformColumnTypes(Params21,{{"Column1", type text}}),
    #"Changed Cont_service14_Type" = Table.TransformColumnTypes(Params22,{{"Column1", type text}}),
    #"Changed Cont_service15_Type" = Table.TransformColumnTypes(Params23,{{"Column1", type text}}),
    #"Changed Cont_Operator7_Type" = Table.TransformColumnTypes(Params24,{{"Column1", type text}}),
    #"Changed Cont_Operator8_Type" = Table.TransformColumnTypes(Params25,{{"Column1", type text}}),
    #"Changed Cont_Operator9_Type" = Table.TransformColumnTypes(Params26,{{"Column1", type text}}),
    #"Changed Cont_Operator10_Type" = Table.TransformColumnTypes(Params27,{{"Column1", type text}}),
    #"Changed Cont_Operator11_Type" = Table.TransformColumnTypes(Params28,{{"Column1", type text}}),
    #"Changed Cont_Operator12_Type" = Table.TransformColumnTypes(Params29,{{"Column1", type text}}),
    #"Changed Cont_Operator13_Type" = Table.TransformColumnTypes(Params30,{{"Column1", type text}}),
    #"Changed Cont_Operator14_Type" = Table.TransformColumnTypes(Params31,{{"Column1", type text}}),
    #"Changed Cont_Operator15_Type" = Table.TransformColumnTypes(Params32,{{"Column1", type text}}),

    // Extract parameter values
    terminal = #"Changed Type_Terminal"{0}[Column1],
    DateFrom = Date.ToText(#"Changed FromDate Type"{0}[Column1], "yyyy-MM-dd"),
    DateTo = Date.ToText(#"Changed ToDate Type"{0}[Column1], "yyyy-MM-dd"),
    operator = #"Changed Cont_Operator_Type"{0}[Column1],
    operator2 = #"Changed Cont_Operator2_Type"{0}[Column1],
    operator3 = #"Changed Cont_Operator3_Type"{0}[Column1],
    operator4 = #"Changed Cont_Operator4_Type"{0}[Column1],
    operator5 = #"Changed Cont_Operator5_Type"{0}[Column1],
    operator6 = #"Changed Cont_Operator6_Type"{0}[Column1],
    service = #"Changed Cont_service_Type"{0}[Column1],
    service2 = #"Changed Cont_service2_Type"{0}[Column1],
    service3 = #"Changed Cont_service3_Type"{0}[Column1],
    service4 = #"Changed Cont_service4_Type"{0}[Column1],
    service5 = #"Changed Cont_service5_Type"{0}[Column1],
    service6 = #"Changed Cont_service6_Type"{0}[Column1],
    service7 = #"Changed Cont_service7_Type"{0}[Column1],
    service8 = #"Changed Cont_service8_Type"{0}[Column1],
    service9 = #"Changed Cont_service9_Type"{0}[Column1],
    service10 = #"Changed Cont_service10_Type"{0}[Column1],
    service11 = #"Changed Cont_service11_Type"{0}[Column1],
    service12 = #"Changed Cont_service12_Type"{0}[Column1],
    service13 = #"Changed Cont_service13_Type"{0}[Column1],
    service14 = #"Changed Cont_service14_Type"{0}[Column1],
    service15 = #"Changed Cont_service15_Type"{0}[Column1],
    operator7 = #"Changed Cont_Operator7_Type"{0}[Column1],
    operator8 = #"Changed Cont_Operator8_Type"{0}[Column1],
    operator9 = #"Changed Cont_Operator9_Type"{0}[Column1],
    operator10 = #"Changed Cont_Operator10_Type"{0}[Column1],
    operator11 = #"Changed Cont_Operator11_Type"{0}[Column1],
    operator12 = #"Changed Cont_Operator12_Type"{0}[Column1],
    operator13= #"Changed Cont_Operator13_Type"{0}[Column1],
    operator14 = #"Changed Cont_Operator14_Type"{0}[Column1],
    operator15 = #"Changed Cont_Operator15_Type"{0}[Column1],


   // Build the dynamic list of operators (only non-empty operators)
    OperatorList = List.Select({operator, operator2, operator3, operator4, operator5, operator6, operator7 , operator8, operator9, operator10, operator11, operator12, operator13, operator14, operator15}, each _ <> "" and _ <> null),

    // Build the dynamic list of services
    ServiceList = List.Select({service, service2, service3, service4, service5, service6, service7, service8, service9, service10, service11, service12, service13, service14, service15}, each _ <> "" and _ <> null),

    OperatorFilter = if List.Count(OperatorList) > 0 then "and container_operator_id IN ('" & Text.Combine(OperatorList, "', '") & "') " else "",
    ServiceFilter = if List.Count(ServiceList) > 0 then "and actual_ob_service_name IN ('" & Text.Combine(ServiceList, "', '") & "') " else "",

    // Construct and execute the SQL query  and container_operator = '" & operator & "' " & unitrequirespowerFilter
    Source = Odbc.Query("dsn=Apache Arrow Flight SQL", 
        "select * from ""APMT-BEATS"".""Global"".""insights_and_visualizations"".""Vessel Moves Insights - Power BI"".""GBL_Shift_on_board_simulator"" 
        where terminalname = '" & terminal & "' 
        and event_date >= '" & DateFrom & "' 
        and event_date <= '" & DateTo & "' 
        " & OperatorFilter & ServiceFilter
        ),
    #"Filtered Rows" = Table.SelectRows(Source, each true)
in
    #"Filtered Rows";