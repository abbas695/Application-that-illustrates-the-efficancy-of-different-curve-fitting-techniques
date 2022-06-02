from statistics import median
from threading import Thread
import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mplcyberpunk import add_glow_effects
from numpy import reshape, linspace, around
from numpy.polynomial import polynomial as p
from pandas import read_csv

plt.style.use('dark_background')
error_arr = []
breakflag = False
drawing = False
countflag = 0
axisdictionary = {'0': ('Overlap', 'Order Of Interpolation', 'Chuncks'),
                  '1': ('Overlap', 'Chuncks', 'Order Of Interpolation'),
                  '2': ('Order Of Interpolation', 'Chuncks', 'Overlap')}


def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw_idle()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


def readfile(file):
    datawave = read_csv(file)
    datawave = [x for x in datawave.iloc[:1000, 0]]
    return datawave


xdata = linspace(0, 1, 1000)


def checkconstant(name1, name2):
    listname = ['chunck_arr', 'degree_arr', 'overlap_arr']
    name3 = [x for x in listname if name1 != x and name2 != x]
    return name3, listname.index(name3[0])


def get_error(true, fitted):
    error = []
    if len(true) == len(fitted):
        for i in range(0, len(fitted)):
            error.append(abs((true[i] - fitted[i]) / true[i]) * 100)
    else:
        if len(fitted) > len(true):
            for i in range(0, len(true)):
                error.append(abs((true[i] - fitted[i]) / true[i]) * 100)
        else:
            for i in range(0, len(fitted)):
                error.append(abs((true[i] - fitted[i]) / true[i]) * 100)
    return error


def get_chuncks(signal, group_size, overlap_size):
    chuncks = [signal[i:i + group_size] for i in range(0, len(signal), group_size - overlap_size)]
    return chuncks


def avrE_singleChunk(chunck, fitted_chunck):
    arr_error = get_error(chunck, fitted_chunck)
    return median(arr_error)


def chuncks(xdata, ydata, overlappingpercentage, noofchuncks, portionofsignal):
    xtrue = []  # Overlapped Xaxis Data
    xdata, ydata, xdataextrapolation = newdata(xdata, ydata, portionofsignal)
    # n is Points per One Chunck
    # m is Overlapping Points
    n = int(len(xdata) / noofchuncks)
    m = int(overlappingpercentage * n)
    if noofchuncks == 1:
        m = 0
    x_chuncks = [xdata[i:i + n] for i in range(0, len(xdata), n - m)]
    y_chuncks = [ydata[i:i + n] for i in range(0, len(ydata), n - m)]
    for i in x_chuncks:
        for k in i:
            xtrue.append(k)
    return x_chuncks, y_chuncks, xdataextrapolation, xtrue


def curvefit(degree, xdata, ydata, overlapping, noofchuncks, portionofsignal):
    ListofCoeff = []
    fittedlist = []
    finallistextrapolation = []
    xchuncks, ychuncks, xdataextrapolation, xtrue = chuncks(xdata, ydata, overlapping, noofchuncks, portionofsignal)
    for i, j in zip(xchuncks, ychuncks):
        ListofCoeff.append(p.polyfit(i, j, int(degree)))
    for i, j in zip(xchuncks, ListofCoeff):
        for k in i:
            fittedlist.append(p.polyval(k, j))
    if noofchuncks == 1:
        for f in xdataextrapolation:
            finallistextrapolation.append(p.polyval(f, ListofCoeff[0]))
    return fittedlist, finallistextrapolation, xtrue, ListofCoeff


def newdata(xdata, ydata, portionofsignal):
    index = int(len(xdata) * portionofsignal)
    xdatanew = xdata[:index + 1]
    ydatanew = ydata[:index + 1]
    xdataextrapolation = xdata[index:]
    return xdatanew, ydatanew, xdataextrapolation


def main():
    sg.theme('Reddit')
    global breakflag
    global drawing
    global countflag
    global axisdictionary

    curvefit_Layout = [
        [sg.Text('Curve Fitting', size=(20, 1), justification='center', font=("Amatic SC", 35),
                 background_color='black',
                 text_color='white')], [sg.Text('Error Map Axes'),
                                        sg.Combo(['overlap_arr/chunck_arr', 'degree_arr/chunck_arr',
                                                  'overlap_arr/degree_arr'], key='choice',
                                                 readonly=True, pad=(20, 0)),
                                        sg.Combo([], size=(10, 5), key='ChunkLatex', pad=(20, 0), readonly=True),
                                        sg.Text('Latex Chunck')],
        [sg.Canvas(size=(340, 50), key='-CANVAS-'),
         sg.Canvas(size=(340, 10), key='-CANVAS2-')],
        [sg.ProgressBar(100, orientation='h', size=(20, 20), key='Progress')],
        [sg.Text('Order Of Interpolation', pad=(35, 0), justification='center'),
         sg.Text('Portion Of Signal', pad=(35, 0), justification='center'),
         sg.Text('Number Of Chuncks', pad=(35, 0), justification='center'),
         sg.Text('Overlap Percentage', pad=(35, 0), justification='center')],
        [sg.Slider(orientation='horizontal', key='Order Of Interpolation', range=(0, 25),
                   enable_events=True, border_width=2, default_value=1),
         sg.Slider(orientation='horizontal', key='Portion', range=(0.01, 1.0),
                   enable_events=True, resolution=0.01, border_width=2, default_value=1.0),
         sg.Slider(orientation='horizontal', key='Chuncks', range=(1, 25),
                   enable_events=True, border_width=2, default_value=1),
         sg.Slider(orientation='horizontal', key='Overlap', range=(0.0, 3.0),
                   enable_events=True, resolution=0.01, border_width=2, default_value=0)],
        [sg.Button('Open File', button_color='black'), sg.Button('Latex', button_color='black'),
         sg.Button('Plot', button_color='black')]]

    curvefit_fig, curvefit_axis = plt.subplots(nrows=2, figsize=(3, 2), constrained_layout=True,
                                      gridspec_kw={'height_ratios': [4, 2]})
    errormap_fig, errormap_axis = plt.subplots(figsize=(4, 2), constrained_layout=True)
    curvefit_axis[1].axis('off')

    CurveFit_window = sg.Window('InterCurve', layout=curvefit_Layout, size=(680, 500), background_color='black', finalize=True,
                       grab_anywhere=True, resizable=True, auto_size_text=True,
                       auto_size_buttons=True, element_justification='center')

    CurveFitFig_agg = draw_figure(CurveFit_window['-CANVAS-'].TKCanvas, curvefit_fig)
    ErrorMapFig_agg = draw_figure(CurveFit_window['-CANVAS2-'].TKCanvas, errormap_fig)
    progress = CurveFit_window['Progress']
    CurveFit_window.bind('<Configure>', 'Event')

    def interpol_extra():
        curvefit_axis[0].cla()
        xdataofplot, ydataofplot, xdataextrapolation = newdata(xdata, ydata, values['Portion'])
        finaldata, finaldataextrapolation, xtrue, ListofCoeff = curvefit(int(values['Order Of Interpolation']), xdata, ydata,
                                                                  values['Overlap'], int(values['Chuncks']),
                                                                  values['Portion'])
        curvefit_axis[0].plot(xdata, ydata, color='orange')
        curvefit_axis[0].set_xlabel('Original')
        curvefit_axis[0].plot(xtrue, finaldata, 'o', markersize=1, color='cyan')
        curvefit_axis[0].set_xlabel('Curve Fitting')
        if int(values['Chuncks']) == 1:
            curvefit_axis[0].plot(xdataextrapolation, finaldataextrapolation)
        curvefit_axis[0].set_ylim(min(ydata) - 0.5, max(ydata) + 0.5)
        curvefit_axis[0].grid()
        add_glow_effects(curvefit_axis[0])
        CurveFitFig_agg.draw_idle()
        return ListofCoeff

    def latex(Parameters):
        FirstLatEq = r'$\ f(x)_{}={} $'
        SecondLatEq = r'$\ + {}X^{}$'
        ThirdLatEq = r'$\ Overall Error = {} $'
        y_dim = 1
        Parameters = around(Parameters, decimals=3)
        ChunkIndex = values['ChunkLatex']
        ChunckParam = Parameters[ChunkIndex]
        x_dim = 0
        curvefit_axis[1].cla()
        curvefit_axis[1].axis('off')
        error = get_OverallError()
        curvefit_axis[1].text((0), y_dim, ThirdLatEq.format(error), size=9, color="white")
        y_dim = y_dim - 0.13
        for i in range(len(ChunckParam)):
            if i == 0:
                curvefit_axis[1].text((0 + x_dim), y_dim, FirstLatEq.format(ChunkIndex, ChunckParam[i]), size=9,
                                      color="white")
                x_dim += 0.04 + float(len(str(ChunckParam[i])) / 55)
                continue
            if i % 3 == 0:
                y_dim = y_dim - 0.1
                x_dim = 0

            curvefit_axis[1].text((0 + x_dim), y_dim, SecondLatEq.format(ChunckParam[i], i), size=9, color="white")
            x_dim += 0.06 + float(len(str(ChunckParam[i])) / 80)

        CurveFitFig_agg.draw_idle()

    def loopOf_chunck(num_chuncks, degree, overlap, xaxis_data, true_signal, choose_case):
        global drawing
        global breakflag
        sumerror = []
        for k in range(0, int(num_chuncks)):
            fit = curvefit(degree, xaxis_data, true_signal, overlap, num_chuncks, 1)
            arr_oftruedata = chuncks(xaxis_data, true_signal, overlap, num_chuncks, 1)
            true_chuncks = arr_oftruedata[1]
            arr_offitteddata = chuncks(xaxis_data, fit[0], overlap, num_chuncks, 1)
            fitted_chuncks = arr_offitteddata[1]
            Average_error = avrE_singleChunk(true_chuncks[k], fitted_chuncks[k])
            sumerror.append(Average_error)
            median_error = median(sumerror)
        if breakflag:
            drawing = False
            return
        error_arr.append(median_error)
        progress.update((num_chuncks / values[axisdictionary.get(str(choose_case))[0]]) * 100)

    def get_OverallError():
        degree = values['Order Of Interpolation']
        overlap = values['Overlap']
        num_chunck = values['Chuncks']
        xaxis_data = xdata
        true_signal = ydata
        sumerror = []
        fit = curvefit(int(degree), xaxis_data, true_signal, int(overlap), int(num_chunck), 1)
        arr_oftruedata = chuncks(xaxis_data, true_signal, overlap, num_chunck, 1)
        true_chuncks = arr_oftruedata[1]
        arr_offitteddata = chuncks(xaxis_data, fit[0], overlap, num_chunck, 1)
        fitted_chuncks = arr_offitteddata[1]
        for k in range(0, int(num_chunck)):
            Average_error = avrE_singleChunk(true_chuncks[k], fitted_chuncks[k])
            sumerror.append(Average_error)
        return median(sumerror)

    def error_map(true_signal, xaxis_data, fixed_parameter, choose_case):
        global breakflag
        global drawing
        global axisdictionary
        drawing = True
        error_arr.clear()
        for i in range(1, int(values[axisdictionary.get(str(choose_case))[0]]) + 1):
            for j in range(0, int(values[axisdictionary.get(str(choose_case))[1]])):
                if choose_case == 0:
                    # Number Of Chuncks Constant
                    # i is Degree Of Interpolation
                    # j is Overlap Percent
                    loopOf_chunck(fixed_parameter, i, j / 100, xaxis_data, true_signal, choose_case)
                    if breakflag:
                        return

                elif choose_case == 1:
                    # Degree Of Interpolation Constant
                    # i Number Of Chuncks
                    # j Overlap Percent
                    # window['Overlap'].update(range=(0.0, 2.0))
                    if i != 0:
                        loopOf_chunck(i, fixed_parameter, j / 100, xaxis_data, true_signal, choose_case)
                        if breakflag:
                            return
                    else:
                        break

                else:
                    # Overlap Percent Constant
                    # i Number Of Chuncks
                    # j Degree Of Interpolation
                    if i != 0:
                        loopOf_chunck(i, j, fixed_parameter, xaxis_data, true_signal, choose_case)
                        if breakflag:
                            return
                    else:
                        break
        return error_arr

    def ploterrormap(x, y, fixedvar, choose_case):
        errormap_fig.clf()
        # values for y and x axis of contour
        lisy = [j for j in range(0, int(values[axisdictionary.get(str(choose_case))[1]]))]
        lisx = [i for i in range(1, int(values[axisdictionary.get(str(choose_case))[0]]) + 1)]
        error_arr = error_map(ydata, xdata, fixedvar, choose_case)
        try:
            err = reshape(error_arr, (len(lisx), len(lisy)))
        except:
            return
        CurveFit_window['Plot'].Update('Plot')
        plt.contourf(lisy, lisx, err, cmap='inferno')
        plt.colorbar()
        plt.xlabel(x)
        plt.ylabel(y)
        ErrorMapFig_agg.draw_idle()

    while True:
        event, values = CurveFit_window.read()
        if event in (sg.WIN_CLOSED, None):
            break
        if event == 'Open File':
            filename = sg.popup_get_file('filename to open', no_window=True, file_types=(("CSV Files", "*.csv"),))
            ydata = readfile(filename)

        if event == 'Event':
            CurveFit_window['-CANVAS-'].expand(True, True)
            CurveFit_window['-CANVAS2-'].expand(True, True)

        if event == 'Plot' and values['choice'] != '' and countflag == 0:
            breakflag = False
            countflag += 1
            CurveFit_window['Plot'].Update('Break')
            x_axisname, y_axisname = values['choice'].split('/')
            constaxis, enablecode = checkconstant(x_axisname, y_axisname)
            Thread(target=ploterrormap,
                   args=[x_axisname, y_axisname, (values[axisdictionary.get(str(enablecode))[2]]), enablecode],
                   daemon=True).start()

        elif event == 'Plot' and drawing == True and countflag == 1:
            breakflag = True
            countflag -= 1
            CurveFit_window['Plot'].Update('Plot')

        if event == 'Latex':
            Thread(target=latex, args=[parameters], daemon=True).start()

        if event in ['Order Of Interpolation', 'Chuncks', 'Overlap', 'Portion']:
            parameters = interpol_extra()
            CurveFit_window['ChunkLatex'].update(values=[i for i in range(int(values['Chuncks']))])
    CurveFit_window.close()


if __name__ == '__main__':
    main()
