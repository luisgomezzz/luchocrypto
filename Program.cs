using IronPython.Hosting;
using Microsoft.Scripting.Hosting;
using System;
using System.xml;

namespace Dynamic
{
    class Program
    {
        static void Main(string[] args)
        {
            ScriptRuntime py = Python.CreateRuntime();
        }
    }
}