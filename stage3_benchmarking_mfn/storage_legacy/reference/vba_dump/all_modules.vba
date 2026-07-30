' ===== MODULE: ThisWorkbook.cls (stream: VBA/ThisWorkbook) =====
Attribute VB_Name = "ThisWorkbook"
Attribute VB_Base = "0{00020819-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
Sub Refreshdata()
ActiveWorkbook.RefreshAll
End Sub


' ===== MODULE: Sheet10.cls (stream: VBA/Sheet10) =====
Attribute VB_Name = "Sheet10"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
Sub Calculate_Revenue_Summary_OOG()
    Dim wsRaw As Worksheet, wsInput As Worksheet
    Dim lastRowRaw As Long, lastRowInput As Long
    Dim rawData As Variant, userInputData As Variant, userInputData2 As Variant
    Dim i As Long, j As Long, k As Long, l As Long
    Dim dwellDays As Long, containerCount As Long, containerLength As Long
    Dim category As String, freightKind As String, method As String
    Dim sumScenarios(0 To 8) As Double
    Dim totalBaseline As Double
    Dim teu As Double
    Dim totalScenario(1 To 8) As Double
    Dim extraDaysRevenue As Double
    Dim matchFound As Boolean, secondMatch As Boolean
    
    ' Disable screen updating, calculations, and events for better performance
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    Application.EnableEvents = False
    
    ' Add category revenue arrays
    Dim importRevenue(0 To 8) As Double
    Dim exportRevenue(0 To 8) As Double
    Dim transhipmentRevenue(0 To 8) As Double
    
    ' Baseline breakdown arrays
    Dim baselineImportRevenue As Double
    Dim baselineExportRevenue As Double
    Dim baselineTranshipmentRevenue As Double
    
    ' Define sheets
    Set wsRaw = ThisWorkbook.Sheets("Raw OOG data")
    Set wsInput = ThisWorkbook.Sheets("Full OOG Storage Simulation")
    
    ' Get the last row in both sheets
    lastRowRaw = wsRaw.Cells(wsRaw.Rows.Count, "A").End(xlUp).Row
    lastRowInput = wsInput.Cells(wsInput.Rows.Count, "E").End(xlUp).Row
    
    ' Load all data into arrays for faster processing
    rawData = wsRaw.Range("A2:M" & lastRowRaw).Value
    userInputData = wsInput.Range("E2:P" & lastRowInput).Value
    
    ' Clear previous data in the summary area but keep formatting.
    wsInput.Range("R1:U53").ClearContents
    
    ' Read user input for calculation method
    method = wsInput.Cells(12, 2).Value
    
    ' Initialize totals to 0
    totalBaseline = 0
    baselineImportRevenue = 0
    baselineExportRevenue = 0
    baselineTranshipmentRevenue = 0
    
    For i = 1 To 8
        totalScenario(i) = 0
        importRevenue(i) = 0
        exportRevenue(i) = 0
        transhipmentRevenue(i) = 0
    Next i
    
    ' Loop through each row in the Raw Data sheet (now in rawData array)
    For i = 1 To UBound(rawData, 1)
        dwellDays = rawData(i, 12) ' Dwell Days
        freightKind = rawData(i, 3) ' Freight Kind
        category = rawData(i, 4) ' Category
        containerCount = rawData(i, 13) ' Container Count
        containerLength = rawData(i, 10) ' Container Length
        If method = "TEU Simple" Then
            If containerLength < 40 Then
                teu = 1
            Else
                teu = 2
            End If
        ElseIf method = "TEU Advanced" Then
            teu = containerLength / 20
        End If
        
        
        ' Reset sumScenarios for each row
        For k = 0 To 8
            sumScenarios(k) = 0
        Next k
        
        ' Find the corresponding row in the User Input sheet (now in userInputData array)
        matchFound = False
        secondMatch = False
        For j = 1 To UBound(userInputData, 1)
            If userInputData(j, 1) = "Day " & dwellDays And userInputData(j, 2) = category Then
                matchFound = True
                Exit For
            End If
        Next j
        
        
        ' If match found, perform the revenue calculations
        If matchFound Then
            ' Calculate revenue based on dwell days
            If dwellDays <= 45 Then
                ' Revenue for dwell days <= 45
                If method = "Container" Then
                    sumScenarios(0) = Application.Sum(wsInput.Range("H" & j - dwellDays + 1 & ":H" & 1 + j)) * containerCount
                
                    For k = 1 To 8
                        sumScenarios(k) = Application.Sum(wsInput.Range(wsInput.Cells(j - dwellDays + 1, 8 + k), wsInput.Cells(1 + j, 8 + k))) * containerCount
                    Next k
                
                Else
                    sumScenarios(0) = Application.Sum(wsInput.Range("H" & j - dwellDays + 1 & ":H" & 1 + j)) * containerCount * teu
                    
                     For k = 1 To 8
                        sumScenarios(k) = Application.Sum(wsInput.Range(wsInput.Cells(j - dwellDays + 1, 8 + k), wsInput.Cells(1 + j, 8 + k))) * containerCount * teu
                    Next k
                End If

            End If
            

        Else
         ' Check if you can find the category / laden combination
         secondMatch = False
         For n = 1 To UBound(userInputData, 1)
            If userInputData(n, 2) = category And userInputData(n, 3) = freightKind Then
                secondMatch = True
                Exit For
            End If
         Next n
                If secondMatch = True Then
                    If method = "Container" Then
                
                           sumScenarios(0) = (Application.Sum(wsInput.Range("H" & n + 1 & ":H" & 46 + n)) + (dwellDays - 45) * wsInput.Cells(46 + n, 8).Value) * containerCount
                           
                        For k = 1 To 8
                            sumScenarios(k) = (Application.Sum(wsInput.Range(wsInput.Cells(n + 1, 8 + k), wsInput.Cells(46 + n, 8 + k))) + (dwellDays - 45) * wsInput.Cells(46 + n, 8 + k).Value) * containerCount
                        Next k
                    Else
                            sumScenarios(0) = (Application.Sum(wsInput.Range("H" & n + 1 & ":H" & 46 + n)) + (dwellDays - 45) * wsInput.Cells(46 + n, 8).Value) * containerCount * teu
                           
                            For k = 1 To 8
                                sumScenarios(k) = (Application.Sum(wsInput.Range(wsInput.Cells(n + 1, 8 + k), wsInput.Cells(46 + n, 8 + k))) + (dwellDays - 45) * wsInput.Cells(46 + n, 8 + k).Value) * containerCount * teu
                            Next k
                    End If
                
                End If



        End If
        
If secondMatch = True Then
    l = n
Else
    l = j
End If

If matchFound = True Or secondMatch = True Then

            Select Case userInputData(l, 2) ' Column F
               Case "Import"
                   baselineImportRevenue = baselineImportRevenue + sumScenarios(0)
                   For k = 1 To 8
                       importRevenue(k) = importRevenue(k) + sumScenarios(k)
                   Next k
               Case "Export"
                   baselineExportRevenue = baselineExportRevenue + sumScenarios(0)
                   For k = 1 To 8
                       exportRevenue(k) = exportRevenue(k) + sumScenarios(k)
                   Next k
               Case "Transshipment"
                   baselineTranshipmentRevenue = baselineTranshipmentRevenue + sumScenarios(0)
                   For k = 1 To 8
                       transhipmentRevenue(k) = transhipmentRevenue(k) + sumScenarios(k)
                   Next k
           End Select
           
            totalBaseline = totalBaseline + sumScenarios(0)
            For k = 1 To 8
                totalScenario(k) = totalScenario(k) + sumScenarios(k)
            Next k
 End If

    Next i
    
Dim outputRow As Long
outputRow = 1 ' Start from row 1
    
    wsInput.Cells(outputRow, 18).Value = "Baseline Revenue"
    wsInput.Cells(outputRow + 1, 18).Value = "Import"
    wsInput.Cells(outputRow + 2, 18).Value = "Export"
    wsInput.Cells(outputRow + 3, 18).Value = "Transhipment"
    wsInput.Cells(outputRow + 4, 18).Value = "Total"
    
    ' Write values for the baseline (Revenue)
    wsInput.Cells(outputRow + 1, 19).Value = baselineImportRevenue
    wsInput.Cells(outputRow + 2, 19).Value = baselineExportRevenue
    wsInput.Cells(outputRow + 3, 19).Value = baselineTranshipmentRevenue
    wsInput.Cells(outputRow + 4, 19).Value = totalBaseline
    
    ' Write the Delta and Delta % for Baseline (they will be 0)
    For i = outputRow + 1 To outputRow + 4
        wsInput.Cells(i, 20).Value = 0 ' Delta
        wsInput.Cells(i, 21).Value = "0%" ' Delta %
    Next i
    
    ' Leave a blank row after Baseline for readability
    outputRow = outputRow + 6
    
    ' Write the summarized results for each scenario with breakdown
    For k = 1 To 8
        wsInput.Cells(outputRow, 18).Value = "Revenue - Scenario " & k
        wsInput.Cells(outputRow + 1, 18).Value = "Import"
        wsInput.Cells(outputRow + 2, 18).Value = "Export"
        wsInput.Cells(outputRow + 3, 18).Value = "Transhipment"
        wsInput.Cells(outputRow + 4, 18).Value = "Total"
        
        ' Write values for the scenario (Revenue, Delta, Delta %)
        wsInput.Cells(outputRow, 19).Value = "Revenue"
        wsInput.Cells(outputRow + 1, 19).Value = importRevenue(k)
        wsInput.Cells(outputRow + 2, 19).Value = exportRevenue(k)
        wsInput.Cells(outputRow + 3, 19).Value = transhipmentRevenue(k)
        wsInput.Cells(outputRow + 4, 19).Value = totalScenario(k) ' Total Revenue - Scenario k
        
        ' Delta Revenue
        wsInput.Cells(outputRow, 20).Value = "Revenue - Delta"
        wsInput.Cells(outputRow + 1, 20).Value = importRevenue(k) - baselineImportRevenue
        wsInput.Cells(outputRow + 2, 20).Value = exportRevenue(k) - baselineExportRevenue
        wsInput.Cells(outputRow + 3, 20).Value = transhipmentRevenue(k) - baselineTranshipmentRevenue
        wsInput.Cells(outputRow + 4, 20).Value = totalScenario(k) - totalBaseline
        
        ' Delta % (Avoid dividing by zero)
        wsInput.Cells(outputRow, 21).Value = "Revenue - Delta %"
        If baselineImportRevenue <> 0 Then
            wsInput.Cells(outputRow + 1, 21).Value = Format((importRevenue(k) - baselineImportRevenue) / baselineImportRevenue, "0.00%")
        Else
            wsInput.Cells(outputRow + 1, 21).Value = "N/A"
        End If
        If baselineExportRevenue <> 0 Then
            wsInput.Cells(outputRow + 2, 21).Value = Format((exportRevenue(k) - baselineExportRevenue) / baselineExportRevenue, "0.00%")
        Else
            wsInput.Cells(outputRow + 2, 21).Value = "N/A"
        End If
        If baselineTranshipmentRevenue <> 0 Then
            wsInput.Cells(outputRow + 3, 21).Value = Format((transhipmentRevenue(k) - baselineTranshipmentRevenue) / baselineTranshipmentRevenue, "0.00%")
        Else
            wsInput.Cells(outputRow + 3, 21).Value = "N/A"
        End If
        If totalBaseline <> 0 Then
            wsInput.Cells(outputRow + 4, 21).Value = Format((totalScenario(k) - totalBaseline) / totalBaseline, "0.00%")
        Else
            wsInput.Cells(outputRow + 4, 21).Value = "N/A"
        End If
        
        outputRow = outputRow + 6 ' Move down 6 rows for the next scenario
    Next k
    
    
    
    ' Re-enable settings after execution
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
    Application.EnableEvents = True
    
        ' Notify user
    MsgBox "Revenue calculation for OOG containers completed!"
End Sub


' ===== MODULE: Sheet11.cls (stream: VBA/Sheet11) =====
Attribute VB_Name = "Sheet11"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
Sub Calculate_Revenue_Summary_Hazardous()
    Dim wsRaw As Worksheet, wsInput As Worksheet
    Dim lastRowRaw As Long, lastRowInput As Long
    Dim rawData As Variant, userInputData As Variant, userInputData2 As Variant
    Dim i As Long, j As Long, k As Long, l As Long
    Dim dwellDays As Long, containerCount As Long, containerLength As Long
    Dim category As String, freightKind As String, method As String
    Dim sumScenarios(0 To 8) As Double
    Dim totalBaseline As Double
    Dim teu As Double
    Dim totalScenario(1 To 8) As Double
    Dim extraDaysRevenue As Double
    Dim matchFound As Boolean, secondMatch As Boolean
    
    ' Disable screen updating, calculations, and events for better performance
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    Application.EnableEvents = False
    
    ' Add category revenue arrays
    Dim importRevenue(0 To 8) As Double
    Dim exportRevenue(0 To 8) As Double
    Dim transhipmentRevenue(0 To 8) As Double
    
    ' Baseline breakdown arrays
    Dim baselineImportRevenue As Double
    Dim baselineExportRevenue As Double
    Dim baselineTranshipmentRevenue As Double
    
    ' Define sheets
    Set wsRaw = ThisWorkbook.Sheets("Raw Hazardous data")
    Set wsInput = ThisWorkbook.Sheets("Full Hazard Storage Simulation")
    
    ' Get the last row in both sheets
    lastRowRaw = wsRaw.Cells(wsRaw.Rows.Count, "A").End(xlUp).Row
    lastRowInput = wsInput.Cells(wsInput.Rows.Count, "E").End(xlUp).Row
    
    ' Load all data into arrays for faster processing
    rawData = wsRaw.Range("A2:M" & lastRowRaw).Value
    userInputData = wsInput.Range("E2:P" & lastRowInput).Value
    
    ' Clear previous data in the summary area but keep formatting.
    wsInput.Range("R1:U53").ClearContents
    
    ' Read user input for calculation method
    method = wsInput.Cells(12, 2).Value
    
    ' Initialize totals to 0
    totalBaseline = 0
    baselineImportRevenue = 0
    baselineExportRevenue = 0
    baselineTranshipmentRevenue = 0
    
    For i = 1 To 8
        totalScenario(i) = 0
        importRevenue(i) = 0
        exportRevenue(i) = 0
        transhipmentRevenue(i) = 0
    Next i
    
    ' Loop through each row in the Raw Data sheet (now in rawData array)
    For i = 1 To UBound(rawData, 1)
        dwellDays = rawData(i, 12) ' Dwell Days
        freightKind = rawData(i, 3) ' Freight Kind
        category = rawData(i, 4) ' Category
        containerCount = rawData(i, 13) ' Container Count
        containerLength = rawData(i, 10) ' Container Length
        If method = "TEU Simple" Then
            If containerLength < 40 Then
                teu = 1
            Else
                teu = 2
            End If
        ElseIf method = "TEU Advanced" Then
            teu = containerLength / 20
        End If
        
        
        ' Reset sumScenarios for each row
        For k = 0 To 8
            sumScenarios(k) = 0
        Next k
        
        ' Find the corresponding row in the User Input sheet (now in userInputData array)
        matchFound = False
        secondMatch = False
        For j = 1 To UBound(userInputData, 1)
            If userInputData(j, 1) = "Day " & dwellDays And userInputData(j, 2) = category Then
                matchFound = True
                Exit For
            End If
        Next j
        
        
        ' If match found, perform the revenue calculations
        If matchFound Then
            ' Calculate revenue based on dwell days
            If dwellDays <= 45 Then
                ' Revenue for dwell days <= 45
                If method = "Container" Then
                    sumScenarios(0) = Application.Sum(wsInput.Range("H" & j - dwellDays + 1 & ":H" & 1 + j)) * containerCount
                
                    For k = 1 To 8
                        sumScenarios(k) = Application.Sum(wsInput.Range(wsInput.Cells(j - dwellDays + 1, 8 + k), wsInput.Cells(1 + j, 8 + k))) * containerCount
                    Next k
                
                Else
                    sumScenarios(0) = Application.Sum(wsInput.Range("H" & j - dwellDays + 1 & ":H" & 1 + j)) * containerCount * teu
                    
                     For k = 1 To 8
                        sumScenarios(k) = Application.Sum(wsInput.Range(wsInput.Cells(j - dwellDays + 1, 8 + k), wsInput.Cells(1 + j, 8 + k))) * containerCount * teu
                    Next k
                End If

            End If
            

        Else
         ' Check if you can find the category / laden combination
         secondMatch = False
         For n = 1 To UBound(userInputData, 1)
            If userInputData(n, 2) = category And userInputData(n, 3) = freightKind Then
                secondMatch = True
                Exit For
            End If
         Next n
                If secondMatch = True Then
                    If method = "Container" Then
                
                           sumScenarios(0) = (Application.Sum(wsInput.Range("H" & n + 1 & ":H" & 46 + n)) + (dwellDays - 45) * wsInput.Cells(46 + n, 8).Value) * containerCount
                           
                        For k = 1 To 8
                            sumScenarios(k) = (Application.Sum(wsInput.Range(wsInput.Cells(n + 1, 8 + k), wsInput.Cells(46 + n, 8 + k))) + (dwellDays - 45) * wsInput.Cells(46 + n, 8 + k).Value) * containerCount
                        Next k
                    Else
                            sumScenarios(0) = (Application.Sum(wsInput.Range("H" & n + 1 & ":H" & 46 + n)) + (dwellDays - 45) * wsInput.Cells(46 + n, 8).Value) * containerCount * teu
                           
                            For k = 1 To 8
                                sumScenarios(k) = (Application.Sum(wsInput.Range(wsInput.Cells(n + 1, 8 + k), wsInput.Cells(46 + n, 8 + k))) + (dwellDays - 45) * wsInput.Cells(46 + n, 8 + k).Value) * containerCount * teu
                            Next k
                    End If
                
                End If



        End If
        
If secondMatch = True Then
    l = n
Else
    l = j
End If

If matchFound = True Or secondMatch = True Then

            Select Case userInputData(l, 2) ' Column F
               Case "Import"
                   baselineImportRevenue = baselineImportRevenue + sumScenarios(0)
                   For k = 1 To 8
                       importRevenue(k) = importRevenue(k) + sumScenarios(k)
                   Next k
               Case "Export"
                   baselineExportRevenue = baselineExportRevenue + sumScenarios(0)
                   For k = 1 To 8
                       exportRevenue(k) = exportRevenue(k) + sumScenarios(k)
                   Next k
               Case "Transshipment"
                   baselineTranshipmentRevenue = baselineTranshipmentRevenue + sumScenarios(0)
                   For k = 1 To 8
                       transhipmentRevenue(k) = transhipmentRevenue(k) + sumScenarios(k)
                   Next k
           End Select
           
            totalBaseline = totalBaseline + sumScenarios(0)
            For k = 1 To 8
                totalScenario(k) = totalScenario(k) + sumScenarios(k)
            Next k
 End If

    Next i
    
Dim outputRow As Long
outputRow = 1 ' Start from row 1
    
    wsInput.Cells(outputRow, 18).Value = "Baseline Revenue"
    wsInput.Cells(outputRow + 1, 18).Value = "Import"
    wsInput.Cells(outputRow + 2, 18).Value = "Export"
    wsInput.Cells(outputRow + 3, 18).Value = "Transhipment"
    wsInput.Cells(outputRow + 4, 18).Value = "Total"
    
    ' Write values for the baseline (Revenue)
    wsInput.Cells(outputRow + 1, 19).Value = baselineImportRevenue
    wsInput.Cells(outputRow + 2, 19).Value = baselineExportRevenue
    wsInput.Cells(outputRow + 3, 19).Value = baselineTranshipmentRevenue
    wsInput.Cells(outputRow + 4, 19).Value = totalBaseline
    
    ' Write the Delta and Delta % for Baseline (they will be 0)
    For i = outputRow + 1 To outputRow + 4
        wsInput.Cells(i, 20).Value = 0 ' Delta
        wsInput.Cells(i, 21).Value = "0%" ' Delta %
    Next i
    
    ' Leave a blank row after Baseline for readability
    outputRow = outputRow + 6
    
    ' Write the summarized results for each scenario with breakdown
    For k = 1 To 8
        wsInput.Cells(outputRow, 18).Value = "Revenue - Scenario " & k
        wsInput.Cells(outputRow + 1, 18).Value = "Import"
        wsInput.Cells(outputRow + 2, 18).Value = "Export"
        wsInput.Cells(outputRow + 3, 18).Value = "Transhipment"
        wsInput.Cells(outputRow + 4, 18).Value = "Total"
        
        ' Write values for the scenario (Revenue, Delta, Delta %)
        wsInput.Cells(outputRow, 19).Value = "Revenue"
        wsInput.Cells(outputRow + 1, 19).Value = importRevenue(k)
        wsInput.Cells(outputRow + 2, 19).Value = exportRevenue(k)
        wsInput.Cells(outputRow + 3, 19).Value = transhipmentRevenue(k)
        wsInput.Cells(outputRow + 4, 19).Value = totalScenario(k) ' Total Revenue - Scenario k
        
        ' Delta Revenue
        wsInput.Cells(outputRow, 20).Value = "Revenue - Delta"
        wsInput.Cells(outputRow + 1, 20).Value = importRevenue(k) - baselineImportRevenue
        wsInput.Cells(outputRow + 2, 20).Value = exportRevenue(k) - baselineExportRevenue
        wsInput.Cells(outputRow + 3, 20).Value = transhipmentRevenue(k) - baselineTranshipmentRevenue
        wsInput.Cells(outputRow + 4, 20).Value = totalScenario(k) - totalBaseline
        
        ' Delta % (Avoid dividing by zero)
        wsInput.Cells(outputRow, 21).Value = "Revenue - Delta %"
        If baselineImportRevenue <> 0 Then
            wsInput.Cells(outputRow + 1, 21).Value = Format((importRevenue(k) - baselineImportRevenue) / baselineImportRevenue, "0.00%")
        Else
            wsInput.Cells(outputRow + 1, 21).Value = "N/A"
        End If
        If baselineExportRevenue <> 0 Then
            wsInput.Cells(outputRow + 2, 21).Value = Format((exportRevenue(k) - baselineExportRevenue) / baselineExportRevenue, "0.00%")
        Else
            wsInput.Cells(outputRow + 2, 21).Value = "N/A"
        End If
        If baselineTranshipmentRevenue <> 0 Then
            wsInput.Cells(outputRow + 3, 21).Value = Format((transhipmentRevenue(k) - baselineTranshipmentRevenue) / baselineTranshipmentRevenue, "0.00%")
        Else
            wsInput.Cells(outputRow + 3, 21).Value = "N/A"
        End If
        If totalBaseline <> 0 Then
            wsInput.Cells(outputRow + 4, 21).Value = Format((totalScenario(k) - totalBaseline) / totalBaseline, "0.00%")
        Else
            wsInput.Cells(outputRow + 4, 21).Value = "N/A"
        End If
        
        outputRow = outputRow + 6 ' Move down 6 rows for the next scenario
    Next k
    
    
    
    ' Re-enable settings after execution
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
    Application.EnableEvents = True
    
        ' Notify user
    MsgBox "Revenue calculation for Hazardous containers completed!"
End Sub



' ===== MODULE: Sheet4.cls (stream: VBA/Sheet4) =====
Attribute VB_Name = "Sheet4"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
''''''''''''''''''''''''''''''''''' New Function only for Reefer Additional income '''''''''''''''''''''''''''''''''''''''''''


Sub Calculate_Revenue_Summary_reefer_electricity()
    Dim wsRaw As Worksheet, wsInput As Worksheet
    Dim lastRowRaw As Long, lastRowInput As Long
    Dim rawData As Variant, userInputData As Variant, userInputData2 As Variant
    Dim i As Long, j As Long, k As Long, l As Long
    Dim dwellDays As Long, containerCount As Long, containerLength As Long
    Dim category As String, freightKind As String, method As String
    Dim sumScenarios_electricity(0 To 8) As Double
    Dim sumScenarios_others(0 To 8) As Double
    Dim totalBaseline As Double
    Dim teu As Double
    Dim totalScenario(1 To 8) As Double
    Dim extraDaysRevenue As Double
    Dim matchFound As Boolean, secondMatch As Boolean
    
    ' Disable screen updating, calculations, and events for better performance
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    Application.EnableEvents = False
    
    ' Add category revenue arrays
    Dim reeferelectricity(0 To 8) As Double
    Dim reeferothers(0 To 8) As Double

    
    ' Baseline breakdown arrays
    Dim baselinereeferelectricity As Double
    Dim baselinereeferothers As Double

    
    ' Define sheets
    Set wsRaw = ThisWorkbook.Sheets("Raw Reefer Data")
    Set wsInput = ThisWorkbook.Sheets("Live Reefer Additional Charges")
    
    ' Get the last row in both sheets
    lastRowRaw = wsRaw.Cells(wsRaw.Rows.Count, "A").End(xlUp).Row
    lastRowInput = wsInput.Cells(wsInput.Rows.Count, "E").End(xlUp).Row
    
    ' Load all data into arrays for faster processing
    rawData = wsRaw.Range("A2:M" & lastRowRaw).Value
    userInputData = wsInput.Range("E2:P" & lastRowInput).Value
    
    ' Clear previous data in the summary area but keep formatting.
    wsInput.Range("R1:U53").ClearContents
    
    ' Read user input for calculation method
    method = wsInput.Cells(12, 2).Value
    
    ' Initialize totals to 0
    totalBaseline = 0
    baselinereeferelectricity = 0
    baselinereeferothers = 0
    
    For i = 1 To 8
        totalScenario(i) = 0
        reeferelectricity(i) = 0
        reeferothers(i) = 0
    Next i
    
    ' Loop through each row in the Raw Data sheet (now in rawData array)
    For i = 1 To UBound(rawData, 1)
        dwellDays = rawData(i, 12) ' Dwell Days
        containerCount = rawData(i, 13) ' Container Count
        containerLength = rawData(i, 10) ' Container Length
        If method = "TEU Simple" Then
            If containerLength < 40 Then
                teu = 1
            Else
                teu = 2
            End If
        ElseIf method = "TEU Advanced" Then
            teu = containerLength / 20
        End If
        
        
        ' Reset sumScenarios for each row
        For k = 0 To 8
            sumScenarios_electricity(k) = 0
            sumScenarios_others(k) = 0
        Next k
        
        ' Find the corresponding row in the User Input sheet (now in userInputData array)
        matchFound = False
        secondMatch = False
        
        ' ELECTRICTY CALCULATIONS

        For j = 1 To UBound(userInputData, 1)
        If userInputData(j, 3) = "Electricity" Then
            If userInputData(j, 1) = "Day " & dwellDays Then
                matchFound = True
                Exit For
            End If
        End If
        Next j
        
        
        ' If match found, perform the revenue calculations
        If matchFound Then
            ' Calculate revenue based on dwell days

                ' Revenue for dwell days <= 45
                If method = "Container" Then
                    sumScenarios_electricity(0) = Application.Sum(wsInput.Range("H" & j - dwellDays + 1 & ":H" & 1 + j)) * containerCount
                
                    For k = 1 To 8
                        sumScenarios_electricity(k) = Application.Sum(wsInput.Range(wsInput.Cells(j - dwellDays + 1, 8 + k), wsInput.Cells(1 + j, 8 + k))) * containerCount
                    Next k
                
                Else
                    sumScenarios_electricity(0) = Application.Sum(wsInput.Range("H" & j - dwellDays + 1 & ":H" & 1 + j)) * containerCount * teu
                    
                     For k = 1 To 8
                        sumScenarios_electricity(k) = Application.Sum(wsInput.Range(wsInput.Cells(j - dwellDays + 1, 8 + k), wsInput.Cells(1 + j, 8 + k))) * containerCount * teu
                    Next k
                End If

            

        Else
         ' Check if you can find the category / laden combination
         secondMatch = False
         For n = 1 To UBound(userInputData, 1)
            If userInputData(n, 3) = "Electricity" Then
                secondMatch = True
                Exit For
            End If
         Next n
                If secondMatch = True Then
                    If method = "Container" Then
                
                           sumScenarios_electricity(0) = (Application.Sum(wsInput.Range("H" & n + 1 & ":H" & 46 + n)) + (dwellDays - 45) * wsInput.Cells(46 + n, 8).Value) * containerCount
                           
                        For k = 1 To 8
                            sumScenarios_electricity(k) = (Application.Sum(wsInput.Range(wsInput.Cells(n + 1, 8 + k), wsInput.Cells(46 + n, 8 + k))) + (dwellDays - 45) * wsInput.Cells(46 + n, 8 + k).Value) * containerCount
                        Next k
                    Else
                            sumScenarios_electricity(0) = (Application.Sum(wsInput.Range("H" & n + 1 & ":H" & 46 + n)) + (dwellDays - 45) * wsInput.Cells(46 + n, 8).Value) * containerCount * teu
                           
                            For k = 1 To 8
                                sumScenarios_electricity(k) = (Application.Sum(wsInput.Range(wsInput.Cells(n + 1, 8 + k), wsInput.Cells(46 + n, 8 + k))) + (dwellDays - 45) * wsInput.Cells(46 + n, 8 + k).Value) * containerCount * teu
                            Next k
                    End If
                
                End If



        End If
        


If matchFound = True Or secondMatch = True Then


    baselinereeferelectricity = baselinereeferelectricity + sumScenarios_electricity(0)
        For k = 1 To 8
            reeferelectricity(k) = reeferelectricity(k) + sumScenarios_electricity(k)
            Next k

           
    totalBaseline = totalBaseline + sumScenarios_electricity(0)
        For k = 1 To 8
            totalScenario(k) = totalScenario(k) + sumScenarios_electricity(k)
        Next k
        
 End If
 
' OTHER CHARGES CALCULATIONS
 



        For j = 1 To UBound(userInputData, 1)
        If userInputData(j, 3) = "Other Charges" Then
            If userInputData(j, 1) = "Day " & dwellDays Then
                matchFound = True
                Exit For
            End If
        End If
        Next j
        
        
        ' If match found, perform the revenue calculations
        If matchFound Then
            ' Calculate revenue based on dwell days

                ' Revenue for dwell days <= 45
                If method = "Container" Then
                    sumScenarios_others(0) = Application.Sum(wsInput.Range("H" & j - dwellDays + 1 & ":H" & 1 + j)) * containerCount
                
                    For k = 1 To 8
                        sumScenarios_others(k) = Application.Sum(wsInput.Range(wsInput.Cells(j - dwellDays + 1, 8 + k), wsInput.Cells(1 + j, 8 + k))) * containerCount
                    Next k
                
                Else
                    sumScenarios_others(0) = Application.Sum(wsInput.Range("H" & j - dwellDays + 1 & ":H" & 1 + j)) * containerCount * teu
                    
                     For k = 1 To 8
                        sumScenarios_others(k) = Application.Sum(wsInput.Range(wsInput.Cells(j - dwellDays + 1, 8 + k), wsInput.Cells(1 + j, 8 + k))) * containerCount * teu
                    Next k
                End If

            

        Else
         ' Check if you can find the category / laden combination
         secondMatch = False
         For n = 1 To UBound(userInputData, 1)
            If userInputData(n, 3) = "Other Charges" Then
                secondMatch = True
                Exit For
            End If
         Next n
                If secondMatch = True Then
                    If method = "Container" Then
                
                           sumScenarios_others(0) = (Application.Sum(wsInput.Range("H" & n + 1 & ":H" & 46 + n)) + (dwellDays - 45) * wsInput.Cells(46 + n, 8).Value) * containerCount
                           
                        For k = 1 To 8
                            sumScenarios_others(k) = (Application.Sum(wsInput.Range(wsInput.Cells(n + 1, 8 + k), wsInput.Cells(46 + n, 8 + k))) + (dwellDays - 45) * wsInput.Cells(46 + n, 8 + k).Value) * containerCount
                        Next k
                    Else
                            sumScenarios_others(0) = (Application.Sum(wsInput.Range("H" & n + 1 & ":H" & 46 + n)) + (dwellDays - 45) * wsInput.Cells(46 + n, 8).Value) * containerCount * teu
                           
                            For k = 1 To 8
                                sumScenarios_others(k) = (Application.Sum(wsInput.Range(wsInput.Cells(n + 1, 8 + k), wsInput.Cells(46 + n, 8 + k))) + (dwellDays - 45) * wsInput.Cells(46 + n, 8 + k).Value) * containerCount * teu
                            Next k
                    End If
                
                End If



        End If
        


If matchFound = True Or secondMatch = True Then


    baselinereeferothers = baselinereeferothers + sumScenarios_others(0)
        For k = 1 To 8
            reeferothers(k) = reeferothers(k) + sumScenarios_others(k)
            Next k

           
    totalBaseline = totalBaseline + sumScenarios_others(0)
        For k = 1 To 8
            totalScenario(k) = totalScenario(k) + sumScenarios_others(k)
        Next k
        
 End If


    Next i
    
Dim outputRow As Long
outputRow = 1 ' Start from row 1
    
    wsInput.Cells(outputRow, 18).Value = "Baseline Revenue"
    wsInput.Cells(outputRow + 1, 18).Value = "Electricity"
    wsInput.Cells(outputRow + 2, 18).Value = "Other Charges"
    wsInput.Cells(outputRow + 3, 18).Value = "Total"
    
    ' Write values for the baseline (Revenue)
    wsInput.Cells(outputRow + 1, 19).Value = baselinereeferelectricity
    wsInput.Cells(outputRow + 2, 19).Value = baselinereeferothers
    wsInput.Cells(outputRow + 3, 19).Value = totalBaseline
    
    ' Write the Delta and Delta % for Baseline (they will be 0)
    For i = outputRow + 1 To outputRow + 4
        wsInput.Cells(i, 20).Value = "" ' Delta
        wsInput.Cells(i, 21).Value = "" ' Delta %
    Next i
    
    ' Leave a blank row after Baseline for readability
    outputRow = outputRow + 6
    
    ' Write the summarized results for each scenario with breakdown
    For k = 1 To 8
        wsInput.Cells(outputRow, 18).Value = "Revenue - Scenario " & k
        wsInput.Cells(outputRow + 1, 18).Value = "Electricity"
        wsInput.Cells(outputRow + 2, 18).Value = "Other Charges"
        wsInput.Cells(outputRow + 3, 18).Value = "Total"
        
        ' Write values for the scenario (Revenue, Delta, Delta %)
        wsInput.Cells(outputRow, 19).Value = "Revenue"
        wsInput.Cells(outputRow + 1, 19).Value = reeferelectricity(k)
        wsInput.Cells(outputRow + 2, 19).Value = reeferothers(k)
        wsInput.Cells(outputRow + 3, 19).Value = totalScenario(k) ' Total Revenue - Scenario k
        
        ' Delta Revenue
        wsInput.Cells(outputRow, 20).Value = "Revenue - Delta"
        wsInput.Cells(outputRow + 1, 20).Value = reeferelectricity(k) - baselinereeferelectricity
        wsInput.Cells(outputRow + 2, 20).Value = reeferothers(k) - baselinereeferothers
        wsInput.Cells(outputRow + 3, 20).Value = totalScenario(k) - totalBaseline
        
        ' Delta % (Avoid dividing by zero)
        wsInput.Cells(outputRow, 21).Value = "Revenue - Delta %"
        If baselinereeferelectricity <> 0 Then
            wsInput.Cells(outputRow + 1, 21).Value = Format((reeferelectricity(k) - baselinereeferelectricity) / baselinereeferelectricity, "0.00%")
        Else
            wsInput.Cells(outputRow + 1, 21).Value = "N/A"
        End If
        If baselinereeferothers <> 0 Then
            wsInput.Cells(outputRow + 2, 21).Value = Format((reeferothers(k) - baselinereeferothers) / baselinereeferothers, "0.00%")
        Else
            wsInput.Cells(outputRow + 2, 21).Value = "N/A"
        End If
        If totalBaseline <> 0 Then
            wsInput.Cells(outputRow + 3, 21).Value = Format((totalScenario(k) - totalBaseline) / totalBaseline, "0.00%")
        Else
            wsInput.Cells(outputRow + 3, 21).Value = "N/A"
        End If
        
        outputRow = outputRow + 6 ' Move down 6 rows for the next scenario
    Next k
    
    
    
    ' Re-enable settings after execution
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
    Application.EnableEvents = True
    
        ' Notify user
    MsgBox "Revenue calculation for additional Reefer charges completed!"
End Sub


' ===== MODULE: Sheet1.cls (stream: VBA/Sheet1) =====
Attribute VB_Name = "Sheet1"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True


' ===== MODULE: Sheet3.cls (stream: VBA/Sheet3) =====
Attribute VB_Name = "Sheet3"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
Sub Calculate_Revenue_Summary_Optimized()
    Dim wsRaw As Worksheet, wsInput As Worksheet
    Dim lastRowRaw As Long, lastRowInput As Long
    Dim rawData As Variant, userInputData As Variant, userInputData2 As Variant
    Dim i As Long, j As Long, k As Long, l As Long
    Dim dwellDays As Long, containerCount As Long, containerLength As Long
    Dim category As String, freightKind As String, method As String
    Dim sumScenarios(0 To 8) As Double
    Dim totalBaseline As Double
    Dim teu As Double
    Dim totalScenario(1 To 8) As Double
    Dim extraDaysRevenue As Double
    Dim matchFound As Boolean, secondMatch As Boolean
    
    ' Disable screen updating, calculations, and events for better performance
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    Application.EnableEvents = False
    
    ' Add category revenue arrays
    Dim importRevenue(0 To 8) As Double
    Dim exportRevenue(0 To 8) As Double
    Dim transhipmentRevenue(0 To 8) As Double
    
    ' Baseline breakdown arrays
    Dim baselineImportRevenue As Double
    Dim baselineExportRevenue As Double
    Dim baselineTranshipmentRevenue As Double
    
    ' Define sheets
    Set wsRaw = ThisWorkbook.Sheets("Raw Dry data")
    Set wsInput = ThisWorkbook.Sheets("Full Dry Storage Simulation")
    
    ' Get the last row in both sheets
    lastRowRaw = wsRaw.Cells(wsRaw.Rows.Count, "A").End(xlUp).Row
    lastRowInput = wsInput.Cells(wsInput.Rows.Count, "E").End(xlUp).Row
    
    ' Load all data into arrays for faster processing
    rawData = wsRaw.Range("A2:M" & lastRowRaw).Value
    userInputData = wsInput.Range("E2:P" & lastRowInput).Value
    
    ' Clear previous data in the summary area but keep formatting.
    wsInput.Range("R1:U53").ClearContents
    
    ' Read user input for calculation method
    method = wsInput.Cells(12, 2).Value
    
    ' Initialize totals to 0
    totalBaseline = 0
    baselineImportRevenue = 0
    baselineExportRevenue = 0
    baselineTranshipmentRevenue = 0
    
    For i = 1 To 8
        totalScenario(i) = 0
        importRevenue(i) = 0
        exportRevenue(i) = 0
        transhipmentRevenue(i) = 0
    Next i
    
    ' Loop through each row in the Raw Data sheet (now in rawData array)
    For i = 1 To UBound(rawData, 1)
        dwellDays = rawData(i, 12) ' Dwell Days
        freightKind = rawData(i, 3) ' Freight Kind
        category = rawData(i, 4) ' Category
        containerCount = rawData(i, 13) ' Container Count
        containerLength = rawData(i, 10) ' Container Length
        If method = "TEU Simple" Then
            If containerLength < 40 Then
                teu = 1
            Else
                teu = 2
            End If
        ElseIf method = "TEU Advanced" Then
            teu = containerLength / 20
        End If
        
        
        ' Reset sumScenarios for each row
        For k = 0 To 8
            sumScenarios(k) = 0
        Next k
        
        ' Find the corresponding row in the User Input sheet (now in userInputData array)
        matchFound = False
        secondMatch = False
        For j = 1 To UBound(userInputData, 1)
            If userInputData(j, 1) = "Day " & dwellDays And userInputData(j, 2) = category Then
                matchFound = True
                Exit For
            End If
        Next j
        
        
        ' If match found, perform the revenue calculations
        If matchFound Then
            ' Calculate revenue based on dwell days
            If dwellDays <= 45 Then
                ' Revenue for dwell days <= 45
                If method = "Container" Then
                    sumScenarios(0) = Application.Sum(wsInput.Range("H" & j - dwellDays + 1 & ":H" & 1 + j)) * containerCount
                
                    For k = 1 To 8
                        sumScenarios(k) = Application.Sum(wsInput.Range(wsInput.Cells(j - dwellDays + 1, 8 + k), wsInput.Cells(1 + j, 8 + k))) * containerCount
                    Next k
                
                Else
                    sumScenarios(0) = Application.Sum(wsInput.Range("H" & j - dwellDays + 1 & ":H" & 1 + j)) * containerCount * teu
                    
                     For k = 1 To 8
                        sumScenarios(k) = Application.Sum(wsInput.Range(wsInput.Cells(j - dwellDays + 1, 8 + k), wsInput.Cells(1 + j, 8 + k))) * containerCount * teu
                    Next k
                End If

            End If
            

        Else
         ' Check if you can find the category / laden combination
         secondMatch = False
         For n = 1 To UBound(userInputData, 1)
            If userInputData(n, 2) = category And userInputData(n, 3) = freightKind Then
                secondMatch = True
                Exit For
            End If
         Next n
                If secondMatch = True Then
                    If method = "Container" Then
                
                           sumScenarios(0) = (Application.Sum(wsInput.Range("H" & n + 1 & ":H" & 46 + n)) + (dwellDays - 45) * wsInput.Cells(46 + n, 8).Value) * containerCount
                           
                        For k = 1 To 8
                            sumScenarios(k) = (Application.Sum(wsInput.Range(wsInput.Cells(n + 1, 8 + k), wsInput.Cells(46 + n, 8 + k))) + (dwellDays - 45) * wsInput.Cells(46 + n, 8 + k).Value) * containerCount
                        Next k
                    Else
                            sumScenarios(0) = (Application.Sum(wsInput.Range("H" & n + 1 & ":H" & 46 + n)) + (dwellDays - 45) * wsInput.Cells(46 + n, 8).Value) * containerCount * teu
                           
                            For k = 1 To 8
                                sumScenarios(k) = (Application.Sum(wsInput.Range(wsInput.Cells(n + 1, 8 + k), wsInput.Cells(46 + n, 8 + k))) + (dwellDays - 45) * wsInput.Cells(46 + n, 8 + k).Value) * containerCount * teu
                            Next k
                    End If
                
                End If



        End If
        
If secondMatch = True Then
    l = n
Else
    l = j
End If

If matchFound = True Or secondMatch = True Then

            Select Case userInputData(l, 2) ' Column F
               Case "Import"
                   baselineImportRevenue = baselineImportRevenue + sumScenarios(0)
                   For k = 1 To 8
                       importRevenue(k) = importRevenue(k) + sumScenarios(k)
                   Next k
               Case "Export"
                   baselineExportRevenue = baselineExportRevenue + sumScenarios(0)
                   For k = 1 To 8
                       exportRevenue(k) = exportRevenue(k) + sumScenarios(k)
                   Next k
               Case "Transshipment"
                   baselineTranshipmentRevenue = baselineTranshipmentRevenue + sumScenarios(0)
                   For k = 1 To 8
                       transhipmentRevenue(k) = transhipmentRevenue(k) + sumScenarios(k)
                   Next k
           End Select
           
            totalBaseline = totalBaseline + sumScenarios(0)
            For k = 1 To 8
                totalScenario(k) = totalScenario(k) + sumScenarios(k)
            Next k
 End If

    Next i
    
Dim outputRow As Long
outputRow = 1 ' Start from row 1
    
    wsInput.Cells(outputRow, 18).Value = "Baseline Revenue"
    wsInput.Cells(outputRow + 1, 18).Value = "Import"
    wsInput.Cells(outputRow + 2, 18).Value = "Export"
    wsInput.Cells(outputRow + 3, 18).Value = "Transhipment"
    wsInput.Cells(outputRow + 4, 18).Value = "Total"
    
    ' Write values for the baseline (Revenue)
    wsInput.Cells(outputRow + 1, 19).Value = baselineImportRevenue
    wsInput.Cells(outputRow + 2, 19).Value = baselineExportRevenue
    wsInput.Cells(outputRow + 3, 19).Value = baselineTranshipmentRevenue
    wsInput.Cells(outputRow + 4, 19).Value = totalBaseline
    
    ' Write the Delta and Delta % for Baseline (they will be 0)
    For i = outputRow + 1 To outputRow + 4
        wsInput.Cells(i, 20).Value = 0 ' Delta
        wsInput.Cells(i, 21).Value = "0%" ' Delta %
    Next i
    
    ' Leave a blank row after Baseline for readability
    outputRow = outputRow + 6
    
    ' Write the summarized results for each scenario with breakdown
    For k = 1 To 8
        wsInput.Cells(outputRow, 18).Value = "Revenue - Scenario " & k
        wsInput.Cells(outputRow + 1, 18).Value = "Import"
        wsInput.Cells(outputRow + 2, 18).Value = "Export"
        wsInput.Cells(outputRow + 3, 18).Value = "Transhipment"
        wsInput.Cells(outputRow + 4, 18).Value = "Total"
        
        ' Write values for the scenario (Revenue, Delta, Delta %)
        wsInput.Cells(outputRow, 19).Value = "Revenue"
        wsInput.Cells(outputRow + 1, 19).Value = importRevenue(k)
        wsInput.Cells(outputRow + 2, 19).Value = exportRevenue(k)
        wsInput.Cells(outputRow + 3, 19).Value = transhipmentRevenue(k)
        wsInput.Cells(outputRow + 4, 19).Value = totalScenario(k) ' Total Revenue - Scenario k
        
        ' Delta Revenue
        wsInput.Cells(outputRow, 20).Value = "Revenue - Delta"
        wsInput.Cells(outputRow + 1, 20).Value = importRevenue(k) - baselineImportRevenue
        wsInput.Cells(outputRow + 2, 20).Value = exportRevenue(k) - baselineExportRevenue
        wsInput.Cells(outputRow + 3, 20).Value = transhipmentRevenue(k) - baselineTranshipmentRevenue
        wsInput.Cells(outputRow + 4, 20).Value = totalScenario(k) - totalBaseline
        
        ' Delta % (Avoid dividing by zero)
        wsInput.Cells(outputRow, 21).Value = "Revenue - Delta %"
        If baselineImportRevenue <> 0 Then
            wsInput.Cells(outputRow + 1, 21).Value = Format((importRevenue(k) - baselineImportRevenue) / baselineImportRevenue, "0.00%")
        Else
            wsInput.Cells(outputRow + 1, 21).Value = "N/A"
        End If
        If baselineExportRevenue <> 0 Then
            wsInput.Cells(outputRow + 2, 21).Value = Format((exportRevenue(k) - baselineExportRevenue) / baselineExportRevenue, "0.00%")
        Else
            wsInput.Cells(outputRow + 2, 21).Value = "N/A"
        End If
        If baselineTranshipmentRevenue <> 0 Then
            wsInput.Cells(outputRow + 3, 21).Value = Format((transhipmentRevenue(k) - baselineTranshipmentRevenue) / baselineTranshipmentRevenue, "0.00%")
        Else
            wsInput.Cells(outputRow + 3, 21).Value = "N/A"
        End If
        If totalBaseline <> 0 Then
            wsInput.Cells(outputRow + 4, 21).Value = Format((totalScenario(k) - totalBaseline) / totalBaseline, "0.00%")
        Else
            wsInput.Cells(outputRow + 4, 21).Value = "N/A"
        End If
        
        outputRow = outputRow + 6 ' Move down 6 rows for the next scenario
    Next k
    
    
    
    ' Re-enable settings after execution
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
    Application.EnableEvents = True
    
        ' Notify user
    MsgBox "Revenue calculation for Dry storage completed!"
End Sub




' ===== MODULE: Sheet9.cls (stream: VBA/Sheet9) =====
Attribute VB_Name = "Sheet9"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
Sub Calculate_Revenue_Summary_Reefer()
    Dim wsRaw As Worksheet, wsInput As Worksheet
    Dim lastRowRaw As Long, lastRowInput As Long
    Dim rawData As Variant, userInputData As Variant, userInputData2 As Variant
    Dim i As Long, j As Long, k As Long, l As Long
    Dim dwellDays As Long, containerCount As Long, containerLength As Long
    Dim category As String, freightKind As String, method As String
    Dim sumScenarios(0 To 8) As Double
    Dim totalBaseline As Double
    Dim teu As Double
    Dim totalScenario(1 To 8) As Double
    Dim extraDaysRevenue As Double
    Dim matchFound As Boolean, secondMatch As Boolean
    
    ' Disable screen updating, calculations, and events for better performance
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    Application.EnableEvents = False
    
    ' Add category revenue arrays
    Dim importRevenue(0 To 8) As Double
    Dim exportRevenue(0 To 8) As Double
    Dim transhipmentRevenue(0 To 8) As Double
    
    ' Baseline breakdown arrays
    Dim baselineImportRevenue As Double
    Dim baselineExportRevenue As Double
    Dim baselineTranshipmentRevenue As Double
    
    ' Define sheets
    Set wsRaw = ThisWorkbook.Sheets("Raw Reefer data")
    Set wsInput = ThisWorkbook.Sheets("Full Reefer Storage Simulation")
    
    ' Get the last row in both sheets
    lastRowRaw = wsRaw.Cells(wsRaw.Rows.Count, "A").End(xlUp).Row
    lastRowInput = wsInput.Cells(wsInput.Rows.Count, "E").End(xlUp).Row
    
    ' Load all data into arrays for faster processing
    rawData = wsRaw.Range("A2:M" & lastRowRaw).Value
    userInputData = wsInput.Range("E2:P" & lastRowInput).Value
    
    ' Clear previous data in the summary area but keep formatting.
    wsInput.Range("R1:U53").ClearContents
    
    ' Read user input for calculation method
    method = wsInput.Cells(12, 2).Value
    
    ' Initialize totals to 0
    totalBaseline = 0
    baselineImportRevenue = 0
    baselineExportRevenue = 0
    baselineTranshipmentRevenue = 0
    
    For i = 1 To 8
        totalScenario(i) = 0
        importRevenue(i) = 0
        exportRevenue(i) = 0
        transhipmentRevenue(i) = 0
    Next i
    
    ' Loop through each row in the Raw Data sheet (now in rawData array)
    For i = 1 To UBound(rawData, 1)
        dwellDays = rawData(i, 12) ' Dwell Days
        freightKind = rawData(i, 3) ' Freight Kind
        category = rawData(i, 4) ' Category
        containerCount = rawData(i, 13) ' Container Count
        containerLength = rawData(i, 10) ' Container Length
        If method = "TEU Simple" Then
            If containerLength < 40 Then
                teu = 1
            Else
                teu = 2
            End If
        ElseIf method = "TEU Advanced" Then
            teu = containerLength / 20
        End If
        
        
        ' Reset sumScenarios for each row
        For k = 0 To 8
            sumScenarios(k) = 0
        Next k
        
        ' Find the corresponding row in the User Input sheet (now in userInputData array)
        matchFound = False
        secondMatch = False
        For j = 1 To UBound(userInputData, 1)
            If userInputData(j, 1) = "Day " & dwellDays And userInputData(j, 2) = category Then
                matchFound = True
                Exit For
            End If
        Next j
        
        
        ' If match found, perform the revenue calculations
        If matchFound Then
            ' Calculate revenue based on dwell days
            If dwellDays <= 45 Then
                ' Revenue for dwell days <= 45
                If method = "Container" Then
                    sumScenarios(0) = Application.Sum(wsInput.Range("H" & j - dwellDays + 1 & ":H" & 1 + j)) * containerCount
                
                    For k = 1 To 8
                        sumScenarios(k) = Application.Sum(wsInput.Range(wsInput.Cells(j - dwellDays + 1, 8 + k), wsInput.Cells(1 + j, 8 + k))) * containerCount
                    Next k
                
                Else
                    sumScenarios(0) = Application.Sum(wsInput.Range("H" & j - dwellDays + 1 & ":H" & 1 + j)) * containerCount * teu
                    
                     For k = 1 To 8
                        sumScenarios(k) = Application.Sum(wsInput.Range(wsInput.Cells(j - dwellDays + 1, 8 + k), wsInput.Cells(1 + j, 8 + k))) * containerCount * teu
                    Next k
                End If

            End If
            

        Else
         ' Check if you can find the category / laden combination
         secondMatch = False
         For n = 1 To UBound(userInputData, 1)
            If userInputData(n, 2) = category And userInputData(n, 3) = freightKind Then
                secondMatch = True
                Exit For
            End If
         Next n
                If secondMatch = True Then
                    If method = "Container" Then
                
                           sumScenarios(0) = (Application.Sum(wsInput.Range("H" & n + 1 & ":H" & 46 + n)) + (dwellDays - 45) * wsInput.Cells(46 + n, 8).Value) * containerCount
                           
                        For k = 1 To 8
                            sumScenarios(k) = (Application.Sum(wsInput.Range(wsInput.Cells(n + 1, 8 + k), wsInput.Cells(46 + n, 8 + k))) + (dwellDays - 45) * wsInput.Cells(46 + n, 8 + k).Value) * containerCount
                        Next k
                    Else
                            sumScenarios(0) = (Application.Sum(wsInput.Range("H" & n + 1 & ":H" & 46 + n)) + (dwellDays - 45) * wsInput.Cells(46 + n, 8).Value) * containerCount * teu
                           
                            For k = 1 To 8
                                sumScenarios(k) = (Application.Sum(wsInput.Range(wsInput.Cells(n + 1, 8 + k), wsInput.Cells(46 + n, 8 + k))) + (dwellDays - 45) * wsInput.Cells(46 + n, 8 + k).Value) * containerCount * teu
                            Next k
                    End If
                
                End If



        End If
        
If secondMatch = True Then
    l = n
Else
    l = j
End If

If matchFound = True Or secondMatch = True Then

            Select Case userInputData(l, 2) ' Column F
               Case "Import"
                   baselineImportRevenue = baselineImportRevenue + sumScenarios(0)
                   For k = 1 To 8
                       importRevenue(k) = importRevenue(k) + sumScenarios(k)
                   Next k
               Case "Export"
                   baselineExportRevenue = baselineExportRevenue + sumScenarios(0)
                   For k = 1 To 8
                       exportRevenue(k) = exportRevenue(k) + sumScenarios(k)
                   Next k
               Case "Transshipment"
                   baselineTranshipmentRevenue = baselineTranshipmentRevenue + sumScenarios(0)
                   For k = 1 To 8
                       transhipmentRevenue(k) = transhipmentRevenue(k) + sumScenarios(k)
                   Next k
           End Select
           
            totalBaseline = totalBaseline + sumScenarios(0)
            For k = 1 To 8
                totalScenario(k) = totalScenario(k) + sumScenarios(k)
            Next k
 End If

    Next i
    
Dim outputRow As Long
outputRow = 1 ' Start from row 1
    
    wsInput.Cells(outputRow, 18).Value = "Baseline Revenue"
    wsInput.Cells(outputRow + 1, 18).Value = "Import"
    wsInput.Cells(outputRow + 2, 18).Value = "Export"
    wsInput.Cells(outputRow + 3, 18).Value = "Transhipment"
    wsInput.Cells(outputRow + 4, 18).Value = "Total"
    
    ' Write values for the baseline (Revenue)
    wsInput.Cells(outputRow + 1, 19).Value = baselineImportRevenue
    wsInput.Cells(outputRow + 2, 19).Value = baselineExportRevenue
    wsInput.Cells(outputRow + 3, 19).Value = baselineTranshipmentRevenue
    wsInput.Cells(outputRow + 4, 19).Value = totalBaseline
    
    ' Write the Delta and Delta % for Baseline (they will be 0)
    For i = outputRow + 1 To outputRow + 4
        wsInput.Cells(i, 20).Value = 0 ' Delta
        wsInput.Cells(i, 21).Value = "0%" ' Delta %
    Next i
    
    ' Leave a blank row after Baseline for readability
    outputRow = outputRow + 6
    
    ' Write the summarized results for each scenario with breakdown
    For k = 1 To 8
        wsInput.Cells(outputRow, 18).Value = "Revenue - Scenario " & k
        wsInput.Cells(outputRow + 1, 18).Value = "Import"
        wsInput.Cells(outputRow + 2, 18).Value = "Export"
        wsInput.Cells(outputRow + 3, 18).Value = "Transhipment"
        wsInput.Cells(outputRow + 4, 18).Value = "Total"
        
        ' Write values for the scenario (Revenue, Delta, Delta %)
        wsInput.Cells(outputRow, 19).Value = "Revenue"
        wsInput.Cells(outputRow + 1, 19).Value = importRevenue(k)
        wsInput.Cells(outputRow + 2, 19).Value = exportRevenue(k)
        wsInput.Cells(outputRow + 3, 19).Value = transhipmentRevenue(k)
        wsInput.Cells(outputRow + 4, 19).Value = totalScenario(k) ' Total Revenue - Scenario k
        
        ' Delta Revenue
        wsInput.Cells(outputRow, 20).Value = "Revenue - Delta"
        wsInput.Cells(outputRow + 1, 20).Value = importRevenue(k) - baselineImportRevenue
        wsInput.Cells(outputRow + 2, 20).Value = exportRevenue(k) - baselineExportRevenue
        wsInput.Cells(outputRow + 3, 20).Value = transhipmentRevenue(k) - baselineTranshipmentRevenue
        wsInput.Cells(outputRow + 4, 20).Value = totalScenario(k) - totalBaseline
        
        ' Delta % (Avoid dividing by zero)
        wsInput.Cells(outputRow, 21).Value = "Revenue - Delta %"
        If baselineImportRevenue <> 0 Then
            wsInput.Cells(outputRow + 1, 21).Value = Format((importRevenue(k) - baselineImportRevenue) / baselineImportRevenue, "0.00%")
        Else
            wsInput.Cells(outputRow + 1, 21).Value = "N/A"
        End If
        If baselineExportRevenue <> 0 Then
            wsInput.Cells(outputRow + 2, 21).Value = Format((exportRevenue(k) - baselineExportRevenue) / baselineExportRevenue, "0.00%")
        Else
            wsInput.Cells(outputRow + 2, 21).Value = "N/A"
        End If
        If baselineTranshipmentRevenue <> 0 Then
            wsInput.Cells(outputRow + 3, 21).Value = Format((transhipmentRevenue(k) - baselineTranshipmentRevenue) / baselineTranshipmentRevenue, "0.00%")
        Else
            wsInput.Cells(outputRow + 3, 21).Value = "N/A"
        End If
        If totalBaseline <> 0 Then
            wsInput.Cells(outputRow + 4, 21).Value = Format((totalScenario(k) - totalBaseline) / totalBaseline, "0.00%")
        Else
            wsInput.Cells(outputRow + 4, 21).Value = "N/A"
        End If
        
        outputRow = outputRow + 6 ' Move down 6 rows for the next scenario
    Next k
    
    
    
    ' Re-enable settings after execution
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
    Application.EnableEvents = True
    
        ' Notify user
    MsgBox "Revenue calculation for basic Reefer storage completed!"
End Sub


' ===== MODULE: Sheet7.cls (stream: VBA/Sheet7) =====
Attribute VB_Name = "Sheet7"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
Private Sub Worksheet_Change(ByVal Target As Range)
    Dim pt As PivotTable
    ' Check if the data range was changed
    If Not Intersect(Target, Me.Range("A:M")) Is Nothing Then
        ' Adjust "Sheet1" to your actual sheet name where the pivot table is located
        With ThisWorkbook.Sheets("Raw OOG Data")
            For Each pt In .PivotTables
                pt.PivotCache.Refresh
            Next pt
        End With
    End If
End Sub




' ===== MODULE: Sheet6.cls (stream: VBA/Sheet6) =====
Attribute VB_Name = "Sheet6"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
Private Sub Worksheet_Change(ByVal Target As Range)
    Dim pt As PivotTable
    ' Check if the data range was changed
    If Not Intersect(Target, Me.Range("A:M")) Is Nothing Then
        ' Adjust "Sheet1" to your actual sheet name where the pivot table is located
        With ThisWorkbook.Sheets("Raw Reefer Data")
            For Each pt In .PivotTables
                pt.PivotCache.Refresh
            Next pt
        End With
    End If
End Sub




' ===== MODULE: Sheet8.cls (stream: VBA/Sheet8) =====
Attribute VB_Name = "Sheet8"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
Private Sub Worksheet_Change(ByVal Target As Range)
    Dim pt As PivotTable
    ' Check if the data range was changed
    If Not Intersect(Target, Me.Range("A:M")) Is Nothing Then
        ' Adjust "Sheet1" to your actual sheet name where the pivot table is located
        With ThisWorkbook.Sheets("Raw Hazardous Data")
            For Each pt In .PivotTables
                pt.PivotCache.Refresh
            Next pt
        End With
    End If
End Sub




' ===== MODULE: Sheet2.cls (stream: VBA/Sheet2) =====
Attribute VB_Name = "Sheet2"
Attribute VB_Base = "0{00020820-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
Private Sub Worksheet_Change(ByVal Target As Range)
    Dim pt As PivotTable
    ' Check if the data range was changed
    If Not Intersect(Target, Me.Range("A:M")) Is Nothing Then
        ' Adjust "Sheet1" to your actual sheet name where the pivot table is located
        With ThisWorkbook.Sheets("Raw Dry Data")
            For Each pt In .PivotTables
                pt.PivotCache.Refresh
            Next pt
        End With
    End If
End Sub


