#include "servergui.h"
#include "ui_servergui.h"

ServerGUI::ServerGUI(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::ServerGUI)
{
    ui->setupUi(this);
}

ServerGUI::~ServerGUI()
{
    delete ui;
}
