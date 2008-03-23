import os
import sys, StringIO

import nose.tools

from doit.dependency import Dependency
from doit.task import InvalidTask, BaseTask, CmdTask, PythonTask
from doit.runner import Runner

# dependencies file
TESTDBM = "testdbm"

class TestVerbosity(object):
 
    # 0: capture stdout and stderr
    def test_verbosity0(self):
        Runner(TESTDBM,0)
        assert BaseTask.CAPTURE_OUT
        assert BaseTask.CAPTURE_ERR

    # 1: capture stderr
    def test_verbosity1(self):
        Runner(TESTDBM,1)
        assert BaseTask.CAPTURE_OUT
        assert not BaseTask.CAPTURE_ERR

    # 2: capture -
    def test_verbosity2(self):
        Runner(TESTDBM,2)
        assert not BaseTask.CAPTURE_OUT
        assert not BaseTask.CAPTURE_ERR



class TestAddTask(object):

    def setUp(self):
        self.runner = Runner(TESTDBM,0)
    
    def test_addTask(self):
        self.runner._addTask(CmdTask("taskX",["ls","bla bla"]))
        self.runner._addTask(CmdTask("taskY",["ls","-1"]))
        assert 2 == len(self.runner._tasks)

    # 2 tasks can not have the same name
    def test_addTaskSameName(self):
        self.runner._addTask(CmdTask("taskX",["ls","bla bla"]))
        t = CmdTask("taskX",["ls","-1"])
        nose.tools.assert_raises(InvalidTask,self.runner._addTask,t)

    def test_addInvalidTask(self):
        nose.tools.assert_raises(InvalidTask,self.runner._addTask,666)




class TestRunningTask(object):
    def setUp(self):
        self.oldOut = sys.stdout
        sys.stdout = StringIO.StringIO()
        self.oldErr = sys.stderr
        sys.stderr = StringIO.StringIO()

    def tearDown(self):
        sys.stdout.close()
        sys.stdout = self.oldOut
        sys.stderr.close()
        sys.stderr = self.oldErr
        if os.path.exists(TESTDBM):
            os.remove(TESTDBM)

    def test_successOutput(self):
        runner = Runner(TESTDBM,1)
        runner._addTask(CmdTask("taskX",["ls", "-1"]))
        runner._addTask(CmdTask("taskY",["ls","-a"]))
        assert runner.SUCCESS == runner.run()
        # only titles are printed.
        taskTitles = sys.stdout.getvalue().split('\n')
        assert runner._tasks['taskX'].title() == taskTitles[0]
        assert runner._tasks['taskY'].title() == taskTitles[1], taskTitles

    # if task is up to date, it is displayed in a different way.
    def test_successUpToDate(self):
        runner = Runner(TESTDBM,1)
        runner._addTask(CmdTask("taskX",["ls", "-1"],dependencies=[__file__]))
        assert runner.SUCCESS == runner.run()
        taskTitles = sys.stdout.getvalue().split('\n')
        assert runner._tasks['taskX'].title() == taskTitles[0]
        # again
        sys.stdout = StringIO.StringIO()
        runner2 = Runner(TESTDBM,1)
        runner2._addTask(CmdTask("taskX",["ls", "-1"],dependencies=[__file__]))
        assert runner2.SUCCESS == runner2.run()
        taskTitles = sys.stdout.getvalue().split('\n')
        assert "--- " +runner2._tasks['taskX'].title() == taskTitles[0]

    # whenever a task fails remaining task are not executed
    def test_failureOutput(self):
        def write_and_fail():
            sys.stdout.write("stdout here.\n")
            sys.stderr.write("stderr here.\n")
            return False

        runner = Runner(TESTDBM,0)
        runner._addTask(PythonTask("taskX",write_and_fail))
        runner._addTask(PythonTask("taskY",write_and_fail))
        assert runner.FAILURE == runner.run()
        output = sys.stdout.getvalue().split('\n')
        assert runner._tasks['taskX'].title() == output[0], output
        # captured output is displayed
        assert "stdout here." == output[1]
        assert "stderr here.\n" == sys.stderr.getvalue()
        # final failed message
        assert "Task failed" == output[2]
        # nothing more (but the empty string)
        assert 4 == len(output)


    def test_errorOutput(self):
        def write_and_error():
            sys.stdout.write("stdout here.\n")
            sys.stderr.write("stderr here.\n")
            raise Exception("I am the exception.\n")

        runner = Runner(TESTDBM,0)
        runner._addTask(PythonTask("taskX",write_and_error))
        runner._addTask(PythonTask("taskY",write_and_error))
        assert runner.ERROR == runner.run()
        output = sys.stdout.getvalue().split('\n')
        errput = sys.stderr.getvalue().split('\n')
        assert runner._tasks['taskX'].title() == output[0], output
        # captured output is displayed
        assert "stdout here." == output[1]
        assert "stderr here." ==  errput[0]
        # final failed message
        assert "Task error" == output[2], output
        # nothing more (but the empty string)
        assert 4 == len(output)

        # FIXME stderr output


    # when successful dependencies are updated
    def test_successDependencies(self):
        filePath = os.path.abspath(__file__+"/../data/dependency1")
        ff = open(filePath,"a")
        ff.write("xxx")
        ff.close()
        dependencies = [filePath]

        filePath = os.path.abspath(__file__+"/../data/target")
        ff = open(filePath,"a")
        ff.write("xxx")
        ff.close()
        targets = [filePath]

        runner = Runner(TESTDBM,1)
        runner._addTask(CmdTask("taskX",["ls", "-1"],dependencies,targets))
        assert runner.SUCCESS == runner.run()
        # only titles are printed.
        d = Dependency(TESTDBM)
        assert 2 == len(d._db)