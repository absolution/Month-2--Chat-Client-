#ifndef CLIENTGUI_H
#define CLIENTGUI_H

#include <QMainWindow>

namespace Ui {
class clientgui;
}

class clientgui : public QMainWindow
{
    Q_OBJECT
    
public:
    explicit clientgui(QWidget *parent = 0);
    ~clientgui();
    
private:
    Ui::clientgui *ui;
};

#endif // CLIENTGUI_H
