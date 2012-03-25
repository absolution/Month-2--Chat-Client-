#ifndef SERVERGUI_H
#define SERVERGUI_H

#include <QMainWindow>

namespace Ui {
class ServerGUI;
}

class ServerGUI : public QMainWindow
{
    Q_OBJECT
    
public:
    explicit ServerGUI(QWidget *parent = 0);
    ~ServerGUI();
    
private:
    Ui::ServerGUI *ui;
};

#endif // SERVERGUI_H
