import wx
import os
import numpy as np
import pyaudio
import wave
import pylab as pl
import struct

LINE_START_POS = 149
LINE_END_POS = 1080


class GUIWindow(wx.Frame):
    def __init__(self, *args, **kw):
        super(GUIWindow, self).__init__(*args, **kw)
        self._v = None
        self._is_playing = False
        self._input_path = None
        self._output_path = None
        self._input_list = []
        self._curr_input_pos = 0
        self._selected_times = []
        self._selected_pos = []

        self.timer = wx.Timer(self)
        self.sld = None
        self.current_array = None
        self._array_flag = []
        self._output_label = None
        self._input_label = None
        self._curr_pos_txt = None
        self._go_to_txt_ctrl = None
        self.curr_size_txt = None
        self.init_ui()

    def init_ui(self):

        # Menu Setting
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        open_item = wx.MenuItem(file_menu, wx.ID_OPEN, text="设定输入路径", kind=wx.ITEM_NORMAL)
        save_item = wx.MenuItem(file_menu, wx.ID_SAVE, text="设定输出路径", kind=wx.ITEM_NORMAL)
        file_menu.Append(open_item)
        file_menu.Append(save_item)
        menu_bar.Append(file_menu, '文件')
        self.SetMenuBar(menu_bar)

        # Layout Setting
        p = wx.Panel(self)

        vertical_box = wx.BoxSizer(wx.VERTICAL)

        self._output_label = wx.StaticText(p, label="当前无输出路径", style=wx.FONTWEIGHT_BOLD | wx.ALIGN_CENTER,
                                           size=(1000, 20))
        self._input_label = wx.StaticText(p, label="当前无输入路径", style=wx.FONTWEIGHT_BOLD | wx.ALIGN_CENTER,
                                          size=(1000, 20))

        vertical_box.Add(self._input_label, 1, wx.ALIGN_CENTER_HORIZONTAL)
        vertical_box.Add(self._output_label, 1, wx.ALIGN_CENTER_HORIZONTAL)

        vertical_box.AddSpacer(20)

        pos_box = wx.BoxSizer(wx.HORIZONTAL)
        self._curr_pos_txt = wx.StaticText(p, size=(70, 20), label="0")
        pos_des_txt = wx.StaticText(p, label="当前位置： ", size=(80, 20))

        size_des_txt = wx.StaticText(p, label="共有音频： ", size=(80, 20))
        self.curr_size_txt = wx.StaticText(p, size=(70, 20), label="0")

        go_to_btn = wx.Button(p, label="转到", size=(30, 30))
        self._go_to_txt_ctrl = wx.TextCtrl(p, size=(70, 20))

        pos_box.Add(pos_des_txt, 0, wx.ALIGN_CENTRE)
        pos_box.Add(self._curr_pos_txt, 0, wx.ALIGN_CENTRE)

        pos_box.Add(size_des_txt, 0, wx.ALIGN_CENTRE)
        pos_box.Add(self.curr_size_txt, 0, wx.ALIGN_CENTRE)

        pos_box.AddSpacer(100)
        pos_box.Add(self._go_to_txt_ctrl, 0, wx.ALIGN_CENTRE)
        pos_box.AddSpacer(20)
        pos_box.Add(go_to_btn, 0, wx.ALIGN_CENTRE)

        vertical_box.Add(pos_box, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL)

        vertical_box.AddSpacer(20)
        self.imgPnl = wx.Panel(p)
        image = wx.Image("tem.png", wx.BITMAP_TYPE_PNG)
        temp = image.ConvertToBitmap()

        self.bmp = wx.StaticBitmap(parent=self.imgPnl, bitmap=temp)
        self.imgPnl.SetSize((1200, 800))
        self.line_btn = wx.Button(self.bmp, label=" ", size=(1, 800), pos=(LINE_END_POS, 0))

        vertical_box.Add(self.imgPnl, 1, wx.ALIGN_CENTER_HORIZONTAL)

        vertical_box.AddSpacer(20)
        self.sld = wx.Slider(p, value=1, minValue=1, maxValue=1000, size=(900, 15))
        vertical_box.Add(self.sld, 0, wx.ALIGN_CENTER_HORIZONTAL)

        vertical_box.AddSpacer(30)

        horizontal_box = wx.BoxSizer(wx.HORIZONTAL)

        play_btn = wx.Button(p, label="播放/暂停")
        horizontal_box.AddSpacer(200)
        horizontal_box.Add(play_btn, 0, wx.ALIGN_CENTER_HORIZONTAL)

        save_btn = wx.Button(p, label="保存")
        horizontal_box.AddStretchSpacer(1)
        horizontal_box.Add(save_btn, 0, wx.ALIGN_LEFT)
        horizontal_box.AddSpacer(100)
        vertical_box.Add(horizontal_box, 1, wx.ALL | wx.EXPAND)

        vertical_box.AddSpacer(50)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)

        add_btn = wx.Button(p, label="添加开始")
        hbox1.AddSpacer(100)
        hbox1.Add(add_btn, 0, wx.ALIGN_CENTER_HORIZONTAL)

        add_end_btn = wx.Button(p, label="添加结束")
        hbox1.AddSpacer(20)
        hbox1.Add(add_end_btn, 0, wx.ALIGN_CENTER_HORIZONTAL)

        hbox1.AddSpacer(20)
        del_btn = wx.Button(p, label="删除")
        hbox1.Add(del_btn, 0, wx.ALIGN_CENTER_HORIZONTAL)

        pre_btn = wx.Button(p, label="上一个")
        hbox1.AddSpacer(500)
        hbox1.Add(pre_btn, 0, wx.ALIGN_LEFT)

        hbox1.AddSpacer(20)
        next_btn = wx.Button(p, label="下一个")
        hbox1.Add(next_btn, 0, wx.ALIGN_LEFT)
        hbox1.AddSpacer(230)
        vertical_box.Add(hbox1, 1, wx.ALL | wx.EXPAND)

        vertical_box.AddSpacer(30)

        text_font = wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False)
        list_data = []
        self.listBox = wx.ListBox(p, -1, pos=(10, 10), size=(600, 120), choices=list_data, style=wx.LB_SINGLE)
        self.listBox.SetFont(text_font)

        vertical_box.Add(self.listBox, 1, wx.ALIGN_CENTER | wx.ALL)
        vertical_box.AddSpacer(50)

        p.SetSizer(vertical_box)

        # Event Binding
        next_btn.Bind(wx.EVT_BUTTON, self.on_next)
        pre_btn.Bind(wx.EVT_BUTTON, self.on_pre)
        play_btn.Bind(wx.EVT_BUTTON, self.on_play)
        save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        add_btn.Bind(wx.EVT_BUTTON, self.on_add_start)
        del_btn.Bind(wx.EVT_BUTTON, self.on_del)
        add_end_btn.Bind(wx.EVT_BUTTON, self.on_add_end)
        go_to_btn.Bind(wx.EVT_BUTTON, self.on_go_to)
        self.listBox.Bind(wx.EVT_LISTBOX, self.on_select)
        self.sld.Bind(wx.EVT_SLIDER, self.on_changed)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.Bind(wx.EVT_MENU, self.on_menu)

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)
        p.SetFocus()
        self.SetFocus()

        self.SetSize((1200, 1000))
        self.Centre()

    def on_go_to(self, e):

        string = self._go_to_txt_ctrl.GetValue().strip()
        if not string.isdigit():
            wx.MessageBox("请输入数字", "Message", wx.OK | wx.ICON_INFORMATION)
            return
        pos = int(string)
        if pos > len(self._input_list):
            wx.MessageBox("输入数字过大，请重新输入", "Message", wx.OK | wx.ICON_INFORMATION)
            return

        self._curr_input_pos = pos - 1
        self.set_curr_input()

    def on_add_end(self, e):
        if not self._v:
            wx.MessageBox("当前没有音频文件", "Message", wx.OK | wx.ICON_INFORMATION)
            return

        time_stamp = self._v.get_len() * self.sld.GetValue() // self.sld.GetMax()
        pos = self.sld.GetValue()

        # No point, definitely no start point
        if len(self._selected_pos) == 0:
            wx.MessageBox("请插入开始点", "Message", wx.OK | wx.ICON_INFORMATION)
            return
        else:
            it = time_stamp - 2
            while True:
                # The previous one is end point
                if it < 0 or self._array_flag[it] == -1:
                    wx.MessageBox("请插入开始点", "Message", wx.OK | wx.ICON_INFORMATION)
                    return
                # There is no point in previous time
                if it < 0:
                    wx.MessageBox("请插入开始点", "Message", wx.OK | wx.ICON_INFORMATION)
                    return

                # Still checking the previous time
                elif self._array_flag[it] == 0:
                    it -= 1
                # Everything is fine, then continue
                else:
                    break

        self._selected_times.append(time_stamp)
        self._selected_times.sort()

        self._selected_pos.append(pos)
        self._selected_pos.sort()
        ind = self._selected_pos.index(pos)

        self._array_flag[time_stamp - 1] = -1

        it = time_stamp - 2

        while it >= 0:
            if self._array_flag[it] > 0:
                # print("Found")
                for i in range(it, time_stamp):
                    self.current_array[i] = 1
                break
            it -= 1

        # print(self._array_flag[it])
        self.flush_fig()
        self.set_list_box()
        self.listBox.SetSelection(ind)

    def on_key(self, e):
        KeyCode = e.GetKeyCode()
        if KeyCode == wx.WXK_DELETE:
            self.del_file()
        elif KeyCode == wx.WXK_CONTROL:
            self.on_del(None)
        elif KeyCode == wx.WXK_LEFT:
            self.on_key_left(None)
        elif KeyCode == wx.WXK_RIGHT:
            self.on_key_right(None)
        elif KeyCode == wx.WXK_SPACE:
            self.on_key_space(None)
        elif KeyCode == 90:
            self.on_add_start(None)
        elif KeyCode == 88:
            self.on_add_end(None)
        elif KeyCode == wx.WXK_SHIFT:
            self.clear_data()
        elif KeyCode == 67:
            self.on_next(None)
        elif KeyCode == 87:
            self.on_pre(None)

        else:
            e.Skip()

    def del_file(self):
        if self._input_path and self._output_path:
            self._v.close()
            os.remove(self._input_list[self._curr_input_pos])

            filename = self._input_list[self._curr_input_pos].split("\\")[-1]
            name = os.path.splitext(filename)[0]
            output_path = self._output_path + "\\" + name + ".npy"
            if os.path.exists(output_path):
                os.remove(output_path)

            del self._input_list[self._curr_input_pos]
            self.set_curr_input()

    def on_select(self, e):
        pos = self.listBox.GetSelection()
        self.sld.SetValue(self._selected_pos[pos])
        self.on_changed(None)

    def on_add_start(self, e):
        if not self._v:
            wx.MessageBox("当前没有音频文件", "Message", wx.OK | wx.ICON_INFORMATION)
            return

        time_stamp = self._v.get_len() * self.sld.GetValue() // self.sld.GetMax()
        pos = self.sld.GetValue()

        if time_stamp in self._selected_times:
            return

        if_print = True
        if (len(self._selected_pos) != 0) and time_stamp != len(self._array_flag):
            it = time_stamp
            while it < len(self._array_flag) - 1:
                if self._array_flag[it + 1] == 1:
                    if_print = False
                    break
                it += 1

        self._selected_times.append(time_stamp)
        self._selected_times.sort()

        self._selected_pos.append(pos)
        self._selected_pos.sort()
        ind = self._selected_pos.index(pos)

        self._array_flag[time_stamp - 1] = 1

        if if_print:
            it = time_stamp
            while True:
                if it >= len(self._array_flag):
                    break
                if self._array_flag[it] == -1:
                    for i in range(time_stamp - 1, it + 1):
                        self.current_array[i] = 1
                    break
                if it < self._v.get_len():
                    it += 1
                else:
                    break

        self.current_array[time_stamp - 1] = 1
        self.flush_fig()
        self.set_list_box()
        self.listBox.SetSelection(ind)

    def set_list_box(self):

        self.listBox.Clear()
        for t in self._selected_times:
            flag = self._array_flag[t - 1]
            if flag > 0:
                string = "开始时间：" + str(t / self._v.get_rate()) + "秒，帧数：" + str(t)
            else:
                string = "结束时间：" + str(t / self._v.get_rate()) + "秒，帧数：" + str(t)
            self.listBox.Append(string)

    def on_del(self, e):
        if not self._v:
            wx.MessageBox("当前没有音频文件", "Message", wx.OK | wx.ICON_INFORMATION)
            return

        if self.listBox.GetSelection() == wx.NOT_FOUND:
            wx.MessageBox("请选中时间点", "Message", wx.OK | wx.ICON_INFORMATION)
            return

        selected_pos = self.listBox.GetSelection()

        # Check Weather it is a start point or end point
        selected_timestamp = self._selected_times[selected_pos]
        flag = self._array_flag[selected_timestamp - 1]

        if flag > 0:
            it = selected_timestamp
            while True:
                if it >= len(self._array_flag) or self._array_flag[it] > 0:
                    break
                elif self._array_flag[it] == 0:
                    it += 1
                else:
                    for i in range(selected_timestamp - 1, it):
                        self.current_array[i] = 0

                    break

        elif flag < 0:
            it = selected_timestamp - 2
            while True:
                if it < 0 or self._array_flag[it] < 0:
                    break
                elif self._array_flag[it] <= 0:
                    it -= 1
                else:
                    for i in range(it + 1, selected_timestamp):
                        self.current_array[i] = 0

                    break

        self._array_flag[selected_timestamp - 1] = 0
        self.current_array[selected_timestamp - 1] = 0

        del (self._selected_pos[selected_pos])
        del (self._selected_times[selected_pos])
        self.set_list_box()
        self.flush_fig()

    def on_menu(self, e):
        if e.GetId() == wx.ID_SAVE:
            dlg = wx.DirDialog(self, u"选择文件夹", style=wx.DD_DEFAULT_STYLE)
            if dlg.ShowModal() == wx.ID_OK:
                self._output_path = dlg.GetPath()
                self.set_curr_input()

        elif e.GetId() == wx.ID_OPEN:
            dlg = wx.DirDialog(self, u"选择文件夹", style=wx.DD_DEFAULT_STYLE)
            if dlg.ShowModal() == wx.ID_OK:
                self._input_path = dlg.GetPath()
                self.set_input_list(self._input_path)
                self.set_curr_input()

    def on_next(self, e):

        if not self._input_path:
            wx.MessageBox("请设置输入路径", "Message", wx.OK | wx.ICON_INFORMATION)
            return
        if not self._output_path:
            wx.MessageBox("请设置输出路径", "Message", wx.OK | wx.ICON_INFORMATION)
            return
        if not self.check_is_valid():
            wx.MessageBox("标记不完全，请检查标记是否完整", "Message", wx.OK | wx.ICON_INFORMATION)
            return
        if len(self._input_list) - 1 <= self._curr_input_pos:
            self._curr_input_pos = len(self._input_list) - 1

            # self.save_as_numpy()
            wx.MessageBox("没有下一个音频文件,若当前有标记，则已保存", "Message", wx.OK | wx.ICON_INFORMATION)
        else:
            self.save_as_numpy()
            self._curr_input_pos += 1
            self._v.close()
            self.listBox.Clear()
            self._selected_times = []
            self._selected_pos = []
            self.set_curr_input()

    def on_pre(self, e):
        if not self._input_path:
            wx.MessageBox("请设置输入路径", "Message", wx.OK | wx.ICON_INFORMATION)
            return
        if not self._output_path:
            wx.MessageBox("请设置输出路径", "Message", wx.OK | wx.ICON_INFORMATION)
            return
        if not self.check_is_valid():
            wx.MessageBox("标记不完全，请检查标记是否完整", "Message", wx.OK | wx.ICON_INFORMATION)
            return

        if 0 >= self._curr_input_pos:
            self._curr_input_pos = 0
            self.save_as_numpy()
            wx.MessageBox("没有上一个音频文件,若当前有标记，则已保存", "Message", wx.OK | wx.ICON_INFORMATION)
        else:
            self.save_as_numpy()
            self._curr_input_pos -= 1
            self._v.close()
            self.listBox.Clear()
            self._selected_times = []
            self._selected_pos = []
            self.set_curr_input()

    def on_changed(self, e):

        if not self._v:
            self.sld.SetValue(1)
        else:
            if self._v.is_active():
                self._v.pause()
                self._is_playing = False
            length = self._v.get_len()
            self._v.set_pos(self._v.get_len() * self.sld.GetValue() // self.sld.GetMax())
            curr_pos_line = round(self._v.get_pos() / length * (LINE_END_POS - LINE_START_POS)) + LINE_START_POS
            self.line_btn.SetPosition((curr_pos_line, 0))
            if self._selected_pos and self.sld.GetValue() in self._selected_pos:
                pos = self._selected_pos.index(self.sld.GetValue())
                self.listBox.SetSelection(pos)

    def on_timer(self, e):
        length = self._v.get_len()
        curr_pos = self._v.get_pos() * self.sld.GetMax() // length
        curr_pos_line = round(self._v.get_pos() / length * (LINE_END_POS - LINE_START_POS)) + LINE_START_POS

        self.sld.SetValue(curr_pos)
        self.line_btn.SetPosition((curr_pos_line, 0))

        if self._v.get_pos() >= length:
            self.timer.Stop()
            self._v.pause()
            # print("stop")
            self._v.set_pos(1)

    def on_play(self, e):
        if not self._v:
            wx.MessageBox("当前没有音频文件", "Message", wx.OK | wx.ICON_INFORMATION)
        elif self._is_playing:
            self._v.pause()
            self.timer.Stop()
            self._is_playing = False
        else:
            self._v.play()
            self.timer.Start()
            self._is_playing = True

    def on_pause(self, e):
        if not self._v:
            wx.MessageBox("当前没有音频文件", "Message", wx.OK | wx.ICON_INFORMATION)
        elif self._is_playing:
            self._v.pause()
            self.timer.Stop()
            self._is_playing = False

    def on_save(self, e):
        if not self._input_path:
            wx.MessageBox("请设置输入路径", "Message", wx.OK | wx.ICON_INFORMATION)
            return
        if not self._output_path:
            wx.MessageBox("请设置输出路径", "Message", wx.OK | wx.ICON_INFORMATION)
            return
        if not self.check_is_valid():
            wx.MessageBox("标记不完全，请检查标记是否完整", "Message", wx.OK | wx.ICON_INFORMATION)
            return
        self.set_curr_input()
        self.save_as_numpy()

    def next_voice(self, path):
        self._v = Voice(path)

    def set_input_list(self, path):
        g = os.walk(path)
        self._input_list = []
        for path, d, filelist in g:
            for filename in filelist:
                if filename.endswith('wav'):
                    # print(os.path.join(path, filename))
                    self._input_list.append(os.path.join(path, filename))

    def on_key_space(self, e):
        self.on_play(None)

    def on_key_right(self, e):
        self.on_pause(None)
        self.sld.SetValue((self.sld.GetValue() + 2) % self.sld.GetMax())
        self.on_changed(None)

    def on_key_left(self, e):
        self.on_pause(None)
        self.sld.SetValue((self.sld.GetValue() - 2) % self.sld.GetMax())
        self.on_changed(None)

    def set_curr_input(self):
        if len(self._input_list) == 0:
            wx.MessageBox("目标文件夹没有音频文件", "Message", wx.OK | wx.ICON_INFORMATION)
        elif len(self._input_list) <= self._curr_input_pos:
            wx.MessageBox("没有下一个音频文件", "Message", wx.OK | wx.ICON_INFORMATION)
            self._curr_input_pos = len(self._input_list) - 1
        else:

            self._v = Voice(self._input_list[self._curr_input_pos])
            self.sld.SetValue(1)
            self._array_flag = np.zeros(self._v.get_len())
            self._selected_times = []
            self._selected_pos = []
            self.listBox.Clear()
            self.current_array = np.zeros(self._v.get_len(), dtype=np.int8)
            self.line_btn.SetPosition((LINE_START_POS, 0))

            self._curr_pos_txt.SetLabel(str(self._curr_input_pos + 1))

            if self._input_path:
                self._input_label.SetLabel("当前输入文件:" + self._input_list[self._curr_input_pos])
                self.curr_size_txt.SetLabel(str(len(self._input_list)))
            else:
                self.curr_size_txt.SetLabel("0")
            if self._output_path:
                self._output_label.SetLabel("当前输出路径:" + self._output_path)

            self.load_exiting_res()
            w = WaveFig(self._input_list[self._curr_input_pos])
            w.add_time(self.current_array)
            w.save_fig()
            image = wx.Image(w.get_fig_name(), wx.BITMAP_TYPE_PNG)
            temp = image.ConvertToBitmap()
            self.bmp.SetBitmap(temp)

    def save_as_numpy(self):
        output = self.current_array
        for i in self._selected_times:
            output[i - 1] = 1

        filename = self._input_list[self._curr_input_pos].split("\\")[-1]
        # name = os.path.splitext(filename)[0]
        name = filename.split(".")[0]
        output_path = self._output_path + "\\" + name + ".label.npy"
        np.save(output_path, output)

    def flush_fig(self):
        w = WaveFig(self._input_list[self._curr_input_pos])
        w.add_time(self.current_array)
        w.save_fig()
        image = wx.Image(w.get_fig_name(), wx.BITMAP_TYPE_PNG)
        temp = image.ConvertToBitmap()
        self.bmp.SetBitmap(temp)

    def clear_data(self):
        for i in range(0, len(self.current_array)):
            self.current_array[i] = 0
            self._array_flag[i] = 0

        self._selected_pos = []
        self._selected_times = []

        self.listBox.Clear()
        self.flush_fig()

    def load_exiting_res(self):
        if self._output_path and self._input_path:
            filename = self._input_list[self._curr_input_pos].split("\\")[-1]
            name = filename.split(".")[0]
            output_path = os.path.join(self._output_path, filename.replace('.wav', ".label.npy"))
            if os.path.exists(output_path):
                curr_array = np.load(output_path)
                self.current_array = curr_array
                is_start = False
                for i in range(0, len(curr_array)):
                    if is_start:
                        if curr_array[i] == 0:
                            is_start = False
                            self._array_flag[i - 1] = -1
                            self._selected_times.append(i)
                            self._selected_pos.append(i * self.sld.GetMax() // len(curr_array))
                    else:
                        if curr_array[i] == 1:
                            is_start = True
                            self._array_flag[i] = 1
                            self._selected_times.append(i + 1)
                            self._selected_pos.append((i + 1) * self.sld.GetMax() // len(curr_array))
                if curr_array[-1] == 1:
                    self._selected_times.append(len(curr_array))
                    self._selected_pos.append(len(curr_array) * self.sld.GetMax() // len(curr_array))
                    self._array_flag[len(curr_array) - 1] = -1

                self.set_list_box()

    def check_is_valid(self):
        if self._array_flag is not None:
            is_start = False
            for flag in self._array_flag:
                if flag == 1 and not is_start:
                    is_start = True
                elif flag == 1 and is_start:
                    return False
                elif flag == -1 and is_start:
                    is_start = False
                elif flag == -1 and not is_start:
                    return False

            if is_start:
                return False
            return True
        else:
            return False


class Voice(object):
    def __init__(self, filename):
        self._wf = wave.open(filename, 'rb')
        self._voice_file = pyaudio.PyAudio()
        self._is_first_play = True
        self.stream = None

    def callback(self, in_data, frame_count, time_info, status):
        data = self._wf.readframes(frame_count)
        return data, pyaudio.paContinue

    def play(self):
        if self._is_first_play:
            self.stream = self._voice_file.open(format=self._voice_file.get_format_from_width(self._wf.getsampwidth()),
                                                channels=self._wf.getnchannels(), rate=self._wf.getframerate(),
                                                output=True, stream_callback=self.callback)
            self._is_first_play = False
        self.stream.start_stream()

    def pause(self):
        if self.stream:
            self.stream.stop_stream()

    def close(self):
        self._wf.close()
        if self.stream:
            self.stream.close()

    def get_pos(self):
        return self._wf.tell()

    def set_pos(self, pos):
        self._wf.setpos(pos)

    def get_len(self):
        return self._wf.getnframes()

    def __delete__(self, instance):
        self.stream.close()
        self._voice_file.terminate()
        self._voice_file.close()

    def is_active(self):
        if self.stream:
            return self.stream.is_active()
        else:
            return False

    def get_rate(self):
        return self._wf.getframerate()

    def get_width(self):
        return self._wf.getsampwidth()


class WaveFig(object):

    def __init__(self, path):
        f = wave.open(path, "rb")
        params = f.getparams()
        nchannels, sampwidth, framerate, nframes = params[:4]
        # str_data = f.readframes(nframes)

        # self._wave_data = np.fromstring(str_data, dtype=np.short)
        #
        # self._rate = framerate
        # self._wave_data.shape = -1, 1
        # self._wave_data = self._wave_data.T

        self._rate = framerate
        self._wave_data = np.zeros(nframes)
        #
        #
        for i in range(nframes):
            val = f.readframes(1)
            left = val[0:2]
            # #right = val[2:4]
            v = struct.unpack('h', left)[0]
            self._wave_data[i] = v

        self._max = np.max(self._wave_data)
        f.close()
        self.time = np.arange(0, nframes) * (1.0 / framerate)
        pl.rcParams['figure.figsize'] = (12.0, 5.0)
        pl.subplot(211)
        pl.xticks([])
        pl.yticks([])
        pl.axis('off')
        pl.xlim(0, np.max(self.time))
        pl.plot(self.time, self._wave_data)
        self._wave_fig_name = "tem.png"

    def add_time(self, array):
        pl.plot(self.time, array * self._max)

    def get_fig_name(self):
        return self._wave_fig_name

    def save_fig(self):
        pl.subplot(212)
        pl.specgram(self._wave_data, Fs=self._rate, cmap=pl.get_cmap("cubehelix"), NFFT=512)
        pl.xticks([])
        pl.yticks([])
        pl.axis('off')
        pl.xlim(0, np.max(self.time))
        pl.savefig(self._wave_fig_name)
        pl.close()


def main():
    app = wx.App()
    ex = GUIWindow(None, -1, style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)
    ex.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()