import wx, traceback

class WizardNavPanel(wx.Panel):

    def __init__(self, wiz, back_btn_enabled=True):
        wx.Panel.__init__(self, wiz)
        self.wiz = wiz
        self.run_btn = wx.Button(self, wx.ID_ANY, 'Run')
        self.back_btn = wx.Button(self, wx.ID_ANY, '<< Back')
        self.back_btn.Enable(back_btn_enabled)
        self.next_btn = wx.Button(self, wx.ID_ANY, 'Next >>')
        self.next_btn.Enable(False)
        self.cancel_btn = wx.Button(self, wx.ID_ANY, 'Cancel')
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.run_btn, 0, wx.ALL|wx.EXPAND, 5)
        btn_sizer.Add(self.back_btn, 0, wx.ALL|wx.EXPAND, 5)
        btn_sizer.Add(self.next_btn, 0, wx.ALL|wx.EXPAND, 5)
        btn_sizer.Add(self.cancel_btn, 0, wx.ALL|wx.EXPAND, 5)
        self.Bind(wx.EVT_BUTTON, self.wiz.on_run, self.run_btn)
        self.Bind(wx.EVT_BUTTON, self.wiz.on_back, self.back_btn)
        self.Bind(wx.EVT_BUTTON, self.wiz.on_next, self.next_btn)
        self.Bind(wx.EVT_BUTTON, self.wiz.on_cancel, self.cancel_btn)
        self.SetSizerAndFit(btn_sizer)

class Wizard(wx.Dialog):

    def __init__(self, parent, title, n_steps, back_btn_enabled=True):
        wx.Dialog.__init__(self, parent, title=title)
        self.parent = parent
        self.n_steps = n_steps
        self.pages = []
        self.curr_page = None
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.nav_pnl = None
        self.model = None
        self.back_btn_enabled = back_btn_enabled

    def add_page(self, page):
        if self.pages:
            self.pages[-1].next = page
            page.prev = self.pages[-1]
        self.pages.append(page)
        page.Hide()
        self.sizer.Add(page, 0, wx.ALL|wx.EXPAND)

    def run(self):
        if not self.nav_pnl:
            self.nav_pnl = WizardNavPanel(self, self.back_btn_enabled)
            self.sizer.Add(self.nav_pnl, 0, wx.ALL|wx.EXPAND, 10)
        for page in self.pages:
            page.is_dirty = True
        self.curr_page = self.pages[0]
        self.curr_page.on_enter(None)
        self.SetSizerAndFit(self.sizer)
        self.Show()

    def on_run(self, e):
        try:
            self.curr_page.on_run(e)
        except:
            wx.EndBusyCursor()
            dlg = wx.MessageDialog(self, traceback.format_exc(),
                                   "Error", wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def on_back(self, e):
        self.curr_page.on_leave(e)
        self.curr_page.prev.on_enter(e)
        self.curr_page = self.curr_page.prev

    def on_next(self, e):
        if self.curr_page == self.pages[-1]:
            self.on_finish(e)
        else:
            self.curr_page.on_leave(e)
            self.curr_page.next.on_enter(e)
            self.curr_page = self.curr_page.next

    def on_cancel(self, e):
        self.curr_page.on_leave(e)
        self.model = None
        self.Hide()

    def on_finish(self, e):
        self.curr_page.Hide()
        self.Hide()

class WizardPage(wx.Panel):

    def __init__(self, wiz, title):
        wx.Panel.__init__(self, wiz)
        self.wiz = wiz
        self.scene = self.wiz.parent.scene
        self.status_bar = self.wiz.parent.status_bar
        self.is_dirty = True
        self.next = self.prev = None
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, wx.ID_ANY, title)
        title.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.AddWindow(title, 0, wx.ALIGN_LEFT|wx.ALL, 10)
        self.sizer.AddWindow(wx.StaticLine(self, wx.ID_ANY), 0,
                             wx.EXPAND|wx.ALL, 5)
        self.SetSizer(self.sizer)

    def update_nav_buttons_and_show(self):
        if self.wiz.back_btn_enabled:
            self.wiz.nav_pnl.back_btn.Enable(self != self.wiz.pages[0])
        self.wiz.nav_pnl.next_btn.Enable(not self.is_dirty)
        self.wiz.nav_pnl.next_btn.SetLabel('Finish'
                                if self == self.wiz.pages[-1] else 'Next >>')
        self.Show()
