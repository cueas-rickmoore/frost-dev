Sub Model()
On Error Resume Next         'this will skip any errors !!!!
'

'
' Keyboard Shortcut: Ctrl+m

 
 Dim T_threshold(2)              'arrays for parameters, 1=endodormancy 2=ecodormancy
 Dim acclimation_rate(2)
 Dim deacclimation_rate(2)
 Dim theta(2)
 
 ' clear output from any previous model run
 
 ' delete any existing charts
 Worksheets("model_output").ChartObjects.Delete
 
 
     Worksheets("model_output").Activate
     
     Range("a2:l260").Select  ' clear model output sheet
     Selection.ClearContents
     Cells(2, 1).Select
     
     
     
' read in parameters from the "input_parameters" sheet

Worksheets("input_parameters").Activate

variety = Cells(2, 1)
Hc_initial = Cells(2, 2)
Hc_min = Cells(2, 3)
Hc_max = Cells(2, 4)
T_threshold(1) = Cells(2, 5)
T_threshold(2) = Cells(2, 6)
ecodormancy_boundary = Cells(2, 7)
acclimation_rate(1) = Cells(2, 8)
acclimation_rate(2) = Cells(2, 9)
deacclimation_rate(1) = Cells(2, 10)
deacclimation_rate(2) = Cells(2, 11)
theta(1) = 1
theta(2) = Cells(2, 12)



'read in year, location, and observed lable from input_temps, only need to do this once
Location = Sheets("input_temps").Cells(2, 4)
Year1 = Sheets("input_temps").Cells(2, 2)    'use variable name Year1 becouse Year is reserved
temp$ = Sheets("input_temps").Cells(1, 8)
                                             'put observed title into model output
Sheets("model_output").Cells(1, 10) = temp$


'calculate range of hardiness values possible, this is needed for the logistic component
Hc_range = Hc_min - Hc_max

'initialize variables for start of model
DD_heating_sum = 0
DD_chilling_sum = 0
base10_chilling_sum = 0
model_Hc_yesterday = Hc_initial
dormancy_period = 1


'**************************************************************************************************


    For j = 2 To 252 'loop thru data
    
                                               'read data from "input_temps" for today
        jdate = Sheets("input_temps").Cells(j, 1)
        jday = Sheets("input_temps").Cells(j, 3)
        T_mean = Sheets("input_temps").Cells(j, 5)
        T_max = Sheets("input_temps").Cells(j, 6)
        T_min = Sheets("input_temps").Cells(j, 7)
        observed_Hc = Sheets("input_temps").Cells(j, 8)
        
        If T_mean = "" Then End                         'terminate program at end of data
        
        
        
        
        
        ' calculate heating degree days for today used in deacclimation
        If T_mean > T_threshold(dormancy_period) Then
            DD_heating_today = T_mean - T_threshold(dormancy_period)
        Else
            DD_heating_today = 0
        End If
        
        
        ' calculate cooling degree days for today used in acclimation
        If T_mean <= T_threshold(dormancy_period) Then
            DD_chilling_today = T_mean - T_threshold(dormancy_period)
        Else
            DD_chilling_today = 0
        End If
        
        
               ' calculate cooling degree days using base of 10c to be used in dormancy release
        If T_mean <= 10 Then
            base10_chilling_today = T_mean - 10
        Else
            base10_chilling_today = 0
        End If
  
        
        ' calculate new model_Hc for today
        
        deacclimation = DD_heating_today * deacclimation_rate(dormancy_period) * (1 - ((model_Hc_yesterday - Hc_max) / Hc_range) ^ theta(dormancy_period))
        
        ' do not allow deacclimation unless some chilling has occured, the actual start of the model
         If DD_chilling_sum = 0 Then deacclimation = 0
        
        acclimation = DD_chilling_today * acclimation_rate(dormancy_period) * (1 - (Hc_min - model_Hc_yesterday) / Hc_range)
        Delta_Hc = acclimation + deacclimation
        model_Hc = model_Hc_yesterday + Delta_Hc
        
        ' limit the hardiness to known min and max
        If model_Hc <= Hc_max Then model_Hc = Hc_max
        If model_Hc > Hc_min Then model_Hc = Hc_min
                
       
        ' sum up chilling degree days
        DD_chilling_sum = DD_chilling_sum + DD_chilling_today
        
        base10_chilling_sum = base10_chilling_sum + base10_chilling_today
        
        ' sum up heating degree days only if chilling requirement has been met
        '  i.e dormancy period 2 has started
        If dormancy_perod = 2 Then DD_heating_sum = DD_heating_sum + DD_heating_today
        
        ' determine if chilling requirement has been met
        ' re-set dormancy period
        ' order of this and other if statements are consistant with Ferguson et al, or V6.3 of our SAS code
        If base10_chilling_sum <= ecodormancy_boundary Then dormancy_period = 2
        
        
        '************* output important data into "model_output" worksheet *********************
        
        Worksheets("model_output").Activate
        Cells(2, 1) = variety
        Cells(2, 2) = Location
        Cells(2, 3) = Year1
        Cells(j, 4) = jdate
        Cells(j, 5) = jday
        Cells(j, 6) = T_mean
        Cells(j, 7) = T_max
        Cells(j, 8) = T_min
        Cells(j, 9) = model_Hc
        Cells(j, 10) = observed_Hc
        
   
        
        
        ' use Hc_min to determine if vinifera or labrusca
        If Hc_min = -1.2 Then    ' assume vinifera with budbreak at -2.2
            If model_Hc_yesterday < -2.2 Then
                If model_Hc >= -2.2 Then
                    Cells(2, 12) = jdate      ' And model_Hc_yesterday < -2.2
                    Cells(j, 11) = model_Hc
                End If
            End If
        End If
        
        If Hc_min = -2.5 Then    'assume labrusca with budbreak at -6.4
            If model_Hc_yesterday < -6.4 Then
                If model_Hc >= -6.4 Then
                    Cells(2, 12) = jdate
                    Cells(j, 11) = model_Hc
                End If
            End If
        End If
        
        
        
        ' remember todays hardiness for tomarrow
        model_Hc_yesterday = model_Hc
 
        
        'Cells(j, 10) = DD_heating_today
        'Cells(j, 11) = DD_chilling_today
        'Cells(j, 12) = dormancy_period
        'Cells(j, 13) = deacclimation
        'Cells(j, 14) = acclimation
        'Cells(j, 15) = DD_chilling_sum
        
    Next j       ' end of data loop
    
 
    
 
End Sub

