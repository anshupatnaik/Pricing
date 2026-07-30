section Section1;

shared #"Storage Raw OOG Data" = let
    // Retrieve parameters from Excel
    Params = Excel.CurrentWorkbook(){[Name="OOGTerminalname"]}[Content],
    DateFromParams = Excel.CurrentWorkbook(){[Name="OOGFrom_date"]}[Content],
    DateToParams = Excel.CurrentWorkbook(){[Name="OOGTo_date"]}[Content],
    Params2 = Excel.CurrentWorkbook(){[Name="OOGContainer_Operator"]}[Content],
    Params4 = Excel.CurrentWorkbook(){[Name="OOGContainer_Operator2"]}[Content],
    Params5 = Excel.CurrentWorkbook(){[Name="OOGContainer_Operator3"]}[Content],
    Params6 = Excel.CurrentWorkbook(){[Name="OOGContainer_Operator4"]}[Content],
    Params7 = Excel.CurrentWorkbook(){[Name="OOGContainer_Operator5"]}[Content],
    Params8 = Excel.CurrentWorkbook(){[Name="OOGContainer_Operator6"]}[Content],
    Params9 = Excel.CurrentWorkbook(){[Name="OOGContainer_Operator7"]}[Content],  
    Params10 = Excel.CurrentWorkbook(){[Name="OOGContainer_Operator8"]}[Content],

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
    #"Changed Cont_Operator7_Type" = Table.TransformColumnTypes(Params9,{{"Column1", type text}}),
    #"Changed Cont_Operator8_Type" = Table.TransformColumnTypes(Params10,{{"Column1", type text}}),

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
    operator7 = #"Changed Cont_Operator7_Type"{0}[Column1],
    operator8 = #"Changed Cont_Operator8_Type"{0}[Column1],


    // Build the dynamic list of operators (only non-empty operators)
    OperatorList = List.Select({operator, operator2, operator3, operator4, operator5, operator6, operator7, operator8}, each _ <> "" and _ <> null),

    OperatorFilter = if List.Count(OperatorList) > 0 then "and container_operator IN ('" & Text.Combine(OperatorList, "', '") & "') " else "",

    // Construct and execute the SQL query  and container_operator = '" & operator & "' " & unitrequirespowerFilter
    Source = Odbc.Query("dsn=Apache Arrow Flight SQL", 
        "select * from ""APMT-BEATS"".""Global"".""insights_and_visualizations"".""Storage Insights - Power BI"".""GBL_Storage_Excel_Simulator"" 
        where terminalname = '" & terminal & "' 
        and month_date >= '" & DateFrom & "' 
        and month_date <= '" & DateTo & "' 
        and freight_kind = 'Full'
        and unit_category_fixed != 'Restow'
        and unit_requires_power = '0' and unit_is_oog = '1' and cargo_is_hazardous = '0'
        " & OperatorFilter
        ),
    #"Filtered Rows" = Table.SelectRows(Source, each true)
in
    #"Filtered Rows";

shared #"Storage Raw Reefer Data" = let
    // Retrieve parameters from Excel
    Params = Excel.CurrentWorkbook(){[Name="ReeferTerminalname"]}[Content],
    DateFromParams = Excel.CurrentWorkbook(){[Name="ReeferFrom_Date"]}[Content],
    DateToParams = Excel.CurrentWorkbook(){[Name="ReeferTo_Date"]}[Content],
    Params2 = Excel.CurrentWorkbook(){[Name="ReeferContainer_Operator"]}[Content],
    Params4 = Excel.CurrentWorkbook(){[Name="ReeferContainer_Operator2"]}[Content],
    Params5 = Excel.CurrentWorkbook(){[Name="ReeferContainer_Operator3"]}[Content],
    Params6 = Excel.CurrentWorkbook(){[Name="ReeferContainer_Operator4"]}[Content],
    Params7 = Excel.CurrentWorkbook(){[Name="ReeferContainer_Operator5"]}[Content],
    Params8 = Excel.CurrentWorkbook(){[Name="ReeferContainer_Operator6"]}[Content],
    Params9 = Excel.CurrentWorkbook(){[Name="ReeferContainer_Operator7"]}[Content],  
    Params10 = Excel.CurrentWorkbook(){[Name="ReeferContainer_Operator8"]}[Content],

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
    #"Changed Cont_Operator7_Type" = Table.TransformColumnTypes(Params9,{{"Column1", type text}}),
    #"Changed Cont_Operator8_Type" = Table.TransformColumnTypes(Params10,{{"Column1", type text}}),

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
    operator7 = #"Changed Cont_Operator7_Type"{0}[Column1],
    operator8 = #"Changed Cont_Operator8_Type"{0}[Column1],

    // Build the dynamic list of operators (only non-empty operators)
    OperatorList = List.Select({operator, operator2, operator3, operator4, operator5, operator6, operator7, operator8}, each _ <> "" and _ <> null),

    OperatorFilter = if List.Count(OperatorList) > 0 then "and container_operator IN ('" & Text.Combine(OperatorList, "', '") & "') " else "",

    // Construct and execute the SQL query  and container_operator = '" & operator & "' " & unitrequirespowerFilter
    Source = Odbc.Query("dsn=Apache Arrow Flight SQL", 
        "select * from ""APMT-BEATS"".""Global"".""insights_and_visualizations"".""Storage Insights - Power BI"".""GBL_Storage_Excel_Simulator"" 
        where terminalname = '" & terminal & "' 
        and month_date >= '" & DateFrom & "' 
        and month_date <= '" & DateTo & "' 
        and freight_kind = 'Full'
        and unit_requires_power = '1'
        and cargo_is_hazardous = '0'
        and unit_category_fixed != 'Restow'
        " & OperatorFilter
        ),
    #"Filtered Rows" = Table.SelectRows(Source, each true)
in
    #"Filtered Rows";

shared #"Storage Raw Hazardous Data" = let
    // Retrieve parameters from Excel
    Params = Excel.CurrentWorkbook(){[Name="HazTerminalname"]}[Content],
    DateFromParams = Excel.CurrentWorkbook(){[Name="HazFrom_Date"]}[Content],
    DateToParams = Excel.CurrentWorkbook(){[Name="HazTo_Date"]}[Content],
    Params2 = Excel.CurrentWorkbook(){[Name="HazContainer_Operator"]}[Content],
    Params4 = Excel.CurrentWorkbook(){[Name="HazContainer_Operator2"]}[Content],
    Params5 = Excel.CurrentWorkbook(){[Name="HazContainer_Operator3"]}[Content],
    Params6 = Excel.CurrentWorkbook(){[Name="HazContainer_Operator4"]}[Content],
    Params7 = Excel.CurrentWorkbook(){[Name="HazContainer_Operator5"]}[Content],
    Params8 = Excel.CurrentWorkbook(){[Name="HazContainer_Operator6"]}[Content],
    Params9 = Excel.CurrentWorkbook(){[Name="HazContainer_Operator7"]}[Content],  
    Params10 = Excel.CurrentWorkbook(){[Name="HazContainer_Operator8"]}[Content],

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
    #"Changed Cont_Operator7_Type" = Table.TransformColumnTypes(Params9,{{"Column1", type text}}),
    #"Changed Cont_Operator8_Type" = Table.TransformColumnTypes(Params10,{{"Column1", type text}}),

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
    operator7 = #"Changed Cont_Operator7_Type"{0}[Column1],
    operator8 = #"Changed Cont_Operator8_Type"{0}[Column1],


    // Build the dynamic list of operators (only non-empty operators)
    OperatorList = List.Select({operator, operator2, operator3, operator4, operator5, operator6, operator7, operator8}, each _ <> "" and _ <> null),

    OperatorFilter = if List.Count(OperatorList) > 0 then "and container_operator IN ('" & Text.Combine(OperatorList, "', '") & "') " else "",

    // Construct and execute the SQL query  and container_operator = '" & operator & "' " & unitrequirespowerFilter
    Source = Odbc.Query("dsn=Apache Arrow Flight SQL", 
        "select * from ""APMT-BEATS"".""Global"".""insights_and_visualizations"".""Storage Insights - Power BI"".""GBL_Storage_Excel_Simulator"" 
        where terminalname = '" & terminal & "' 
        and month_date >= '" & DateFrom & "' 
        and month_date <= '" & DateTo & "' 
        and freight_kind = 'Full'
        and unit_category_fixed != 'Restow'
        and unit_is_oog = '0' and cargo_is_hazardous = '1'
        " & OperatorFilter
        ),
    #"Filtered Rows" = Table.SelectRows(Source, each true)
in
    #"Filtered Rows";

shared #"Storage Raw Dry Data" = let
    // Retrieve parameters from Excel
    Params = Excel.CurrentWorkbook(){[Name="Terminalname"]}[Content],
    DateFromParams = Excel.CurrentWorkbook(){[Name="From_Date"]}[Content],
    DateToParams = Excel.CurrentWorkbook(){[Name="To_Date"]}[Content],
    Params2 = Excel.CurrentWorkbook(){[Name="Container_Operator"]}[Content],
    Params4 = Excel.CurrentWorkbook(){[Name="Container_Operator_2"]}[Content],
    Params5 = Excel.CurrentWorkbook(){[Name="Container_Operator_3"]}[Content],
    Params6 = Excel.CurrentWorkbook(){[Name="Container_Operator_4"]}[Content],
    Params7 = Excel.CurrentWorkbook(){[Name="Container_Operator_5"]}[Content],
    Params8 = Excel.CurrentWorkbook(){[Name="Container_Operator_6"]}[Content],
    Params9 = Excel.CurrentWorkbook(){[Name="Container_Operator_7"]}[Content],  
    Params10 = Excel.CurrentWorkbook(){[Name="Container_Operator_8"]}[Content],

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
    #"Changed Cont_Operator7_Type" = Table.TransformColumnTypes(Params9,{{"Column1", type text}}),
    #"Changed Cont_Operator8_Type" = Table.TransformColumnTypes(Params10,{{"Column1", type text}}),

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
    operator7 = #"Changed Cont_Operator7_Type"{0}[Column1],
    operator8 = #"Changed Cont_Operator8_Type"{0}[Column1],


    // Build the dynamic list of operators (only non-empty operators)
    OperatorList = List.Select({operator, operator2, operator3, operator4, operator5, operator6, operator7, operator8}, each _ <> "" and _ <> null),

    OperatorFilter = if List.Count(OperatorList) > 0 then "and container_operator IN ('" & Text.Combine(OperatorList, "', '") & "') " else "",

    // Construct and execute the SQL query  and container_operator = '" & operator & "' " & unitrequirespowerFilter
    Source = Odbc.Query("dsn=Apache Arrow Flight SQL", 
        "select * from ""APMT-BEATS"".""Global"".""insights_and_visualizations"".""Storage Insights - Power BI"".""GBL_Storage_Excel_Simulator"" 
        where terminalname = '" & terminal & "' 
        and month_date >= '" & DateFrom & "' 
        and month_date <= '" & DateTo & "' 
        and freight_kind = 'Full'
        and unit_category_fixed != 'Restow'
        and unit_is_oog = '0' and cargo_is_hazardous = '0' and unit_requires_power = '0'
        " & OperatorFilter
        ),
    #"Filtered Rows" = Table.SelectRows(Source, each true)
in
    #"Filtered Rows";