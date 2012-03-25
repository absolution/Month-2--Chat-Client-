#include "clientgui.h"
#include "ui_clientgui.h"

clientgui::clientgui(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::clientgui)
{
    ui->setupUi(this);
}

clientgui::~clientgui()
{
    delete ui;
}
