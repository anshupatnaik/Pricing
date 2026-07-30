'== ThisWorkbook.cls ==
Attribute VB_Name = "ThisWorkbook"
Attribute VB_Base = "0{00020819-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet4.cls ==
Attribute VB_Name = "Sheet4"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet5.cls ==
Attribute VB_Name = "Sheet5"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet1.cls ==
Attribute VB_Name = "Sheet1"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet6.cls ==
Attribute VB_Name = "Sheet6"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
Sub RefreshButton_Click()
    ActiveWorkbook.RefreshAll
End Sub





'== Sheet11.cls ==
Attribute VB_Name = "Sheet11"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet7.cls ==
Attribute VB_Name = "Sheet7"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet8.cls ==
Attribute VB_Name = "Sheet8"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet3.cls ==
Attribute VB_Name = "Sheet3"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet17.cls ==
Attribute VB_Name = "Sheet17"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet9.cls ==
Attribute VB_Name = "Sheet9"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet10.cls ==
Attribute VB_Name = "Sheet10"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet12.cls ==
Attribute VB_Name = "Sheet12"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet13.cls ==
Attribute VB_Name = "Sheet13"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet14.cls ==
Attribute VB_Name = "Sheet14"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet15.cls ==
Attribute VB_Name = "Sheet15"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
Sub PopulateUniqueSLRatesAndOccurrences()
    Dim wsSource As Worksheet
    Dim wsTarget As Worksheet
    Dim lastRowSource As Long
    Dim rowNum As Long
    Dim i As Long
    Dim imoIndicator As String
    Dim cargoIMDGType As String
    Dim concatenatedValue As String
    Dim cargoArray As Variant
    Dim roundedCargoTypes As String
    Dim j As Long
    Dim uniqueDict As Object ' Dictionary to hold unique combinations
    Dim sumDict As Object ' Dictionary to hold the sum of column U for each unique combination
    Dim valueU As Double

    ' Set the source and target worksheets
    Set wsSource = ThisWorkbook.Sheets("Moves Raw data")
    Set wsTarget = ThisWorkbook.Sheets("Automatic Ocurrences")
    
    ' Clear rows 228 onwards in the target sheet
    wsTarget.Rows("228:" & wsTarget.Rows.Count).ClearContents
    
    ' Initialize dictionaries for unique combinations and sums
    Set uniqueDict = CreateObject("Scripting.Dictionary")
    Set sumDict = CreateObject("Scripting.Dictionary")
    
    ' Find the last row in the source sheet
    lastRowSource = wsSource.Cells(wsSource.Rows.Count, 7).End(xlUp).Row ' Column G (imo_indicator)
    
    ' Start writing to the target sheet from row 228
    rowNum = 228
    
    ' Loop through the rows in the source sheet
    For i = 2 To lastRowSource ' Assuming there's a header in row 1
        imoIndicator = wsSource.Cells(i, 7).Value ' Column G (imo_indicator)
        cargoIMDGType = wsSource.Cells(i, 8).Value ' Column H (cargo_imdg_types)
        valueU = wsSource.Cells(i, 21).Value ' Column U (values to sum)
        
        ' Only process if neither imoIndicator nor cargoIMDGType is empty
        If imoIndicator <> "" And cargoIMDGType <> "" Then
            ' Split the cargo IMDG types by comma, round the values, and rejoin them
            cargoArray = Split(cargoIMDGType, ",")
            roundedCargoTypes = ""

            ' Loop through the cargoArray and round each value
            For j = LBound(cargoArray) To UBound(cargoArray)
                If IsNumeric(Trim(cargoArray(j))) Then
                    ' Round the cargo IMDG type to the nearest integer
                    roundedCargoTypes = roundedCargoTypes & Int(Trim(cargoArray(j))) & ","
                End If
            Next j

            ' Remove the trailing comma
            If Len(roundedCargoTypes) > 0 Then
                roundedCargoTypes = Left(roundedCargoTypes, Len(roundedCargoTypes) - 1)
            End If
            
            ' Concatenate the IMO indicator and rounded cargo IMDG types with " Load/Discharge"
            concatenatedValue = imoIndicator & " " & roundedCargoTypes & " Load/Discharge"
            
            ' Check if this combination is already added to the dictionary
            If Not uniqueDict.exists(concatenatedValue) Then
                ' Add the concatenated value to the dictionary as a unique entry
                uniqueDict.Add concatenatedValue, True
                ' Initialize the sum for this combination in sumDict
                sumDict.Add concatenatedValue, valueU
            Else
                ' If the combination already exists, update the sum
                sumDict(concatenatedValue) = sumDict(concatenatedValue) + valueU
            End If
        End If
    Next i
    
    ' Output unique combinations and their sums to the target sheet
    Dim key As Variant
    For Each key In uniqueDict.Keys
        ' Write values to the target sheet
        wsTarget.Cells(rowNum, 1).Value = rowNum - 1 ' Column A (row_number - 1)
        wsTarget.Cells(rowNum, 2).Value = "Surcharge - Hazardous Cargo" ' Column B
        wsTarget.Cells(rowNum, 3).Value = key ' Column C
        wsTarget.Cells(rowNum, 4).Value = "NO" ' Column D
        wsTarget.Cells(rowNum, 5).Value = sumDict(key) ' Column E (sum of values from column U)
        
        ' Increment the row number for the target sheet
        rowNum = rowNum + 1
    Next key

End Sub




'== Sheet20.cls ==
Attribute VB_Name = "Sheet20"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


'== Sheet16.cls ==
Attribute VB_Name = "Sheet16"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
Sub PopulateUniqueSLRatesAndOccurrences()
    Dim wsSource As Worksheet
    Dim wsTarget As Worksheet
    Dim lastRowSource As Long
    Dim rowNum As Long
    Dim i As Long
    Dim imoIndicator As String
    Dim cargoIMDGType As String
    Dim concatenatedValue As String
    Dim cargoArray As Variant
    Dim roundedCargoTypes As String
    Dim j As Long
    Dim uniqueDict As Object ' Dictionary to hold unique combinations
    Dim sumDict As Object ' Dictionary to hold the sum of column U for each unique combination
    Dim valueU As Double

    ' Set the source and target worksheets
    Set wsSource = ThisWorkbook.Sheets("Moves Raw data")
    Set wsTarget = ThisWorkbook.Sheets("SL Rates and Ocurrences")
    
    ' Clear rows 228 onwards in the target sheet
    wsTarget.Rows("228:" & wsTarget.Rows.Count).ClearContents
    
    ' Initialize dictionaries for unique combinations and sums
    Set uniqueDict = CreateObject("Scripting.Dictionary")
    Set sumDict = CreateObject("Scripting.Dictionary")
    
    ' Find the last row in the source sheet
    lastRowSource = wsSource.Cells(wsSource.Rows.Count, 7).End(xlUp).Row ' Column G (imo_indicator)
    
    ' Start writing to the target sheet from row 228
    rowNum = 228
    
    ' Loop through the rows in the source sheet
    For i = 2 To lastRowSource ' Assuming there's a header in row 1
        imoIndicator = wsSource.Cells(i, 7).Value ' Column G (imo_indicator)
        cargoIMDGType = wsSource.Cells(i, 8).Value ' Column H (cargo_imdg_types)
        valueU = wsSource.Cells(i, 21).Value ' Column U (values to sum)
        
        ' Only process if neither imoIndicator nor cargoIMDGType is empty
        If imoIndicator <> "" And cargoIMDGType <> "" Then
            ' Split the cargo IMDG types by comma, round the values, and rejoin them
            cargoArray = Split(cargoIMDGType, ",")
            roundedCargoTypes = ""

            ' Loop through the cargoArray and round each value
            For j = LBound(cargoArray) To UBound(cargoArray)
                If IsNumeric(Trim(cargoArray(j))) Then
                    ' Round the cargo IMDG type to the nearest integer
                    roundedCargoTypes = roundedCargoTypes & Int(Trim(cargoArray(j))) & ","
                End If
            Next j

            ' Remove the trailing comma
            If Len(roundedCargoTypes) > 0 Then
                roundedCargoTypes = Left(roundedCargoTypes, Len(roundedCargoTypes) - 1)
            End If
            
            ' Concatenate the IMO indicator and rounded cargo IMDG types with " Load/Discharge"
            concatenatedValue = imoIndicator & " " & roundedCargoTypes & " Load/Discharge"
            
            ' Check if this combination is already added to the dictionary
            If Not uniqueDict.exists(concatenatedValue) Then
                ' Add the concatenated value to the dictionary as a unique entry
                uniqueDict.Add concatenatedValue, True
                ' Initialize the sum for this combination in sumDict
                sumDict.Add concatenatedValue, valueU
            Else
                ' If the combination already exists, update the sum
                sumDict(concatenatedValue) = sumDict(concatenatedValue) + valueU
            End If
        End If
    Next i
    
    ' Output unique combinations and their sums to the target sheet
    Dim key As Variant
    For Each key In uniqueDict.Keys
        ' Write values to the target sheet
        wsTarget.Cells(rowNum, 1).Value = rowNum - 1 ' Column A (row_number - 1)
        wsTarget.Cells(rowNum, 2).Value = "Surcharge - Hazardous Cargo" ' Column B
        wsTarget.Cells(rowNum, 3).Value = key ' Column C
        wsTarget.Cells(rowNum, 4).Value = "NO" ' Column D
        wsTarget.Cells(rowNum, 5).Value = sumDict(key) ' Column E (sum of values from column U)
        
        ' Increment the row number for the target sheet
        rowNum = rowNum + 1
    Next key

End Sub




'== Sheet2.cls ==
Attribute VB_Name = "Sheet2"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
