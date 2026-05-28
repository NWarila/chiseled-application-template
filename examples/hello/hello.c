/*
 * Trivial reference application for chiseled-application-template.
 *
 * Credential-free and dependency-free on purpose: it builds to a small static
 * binary so the only thing under test is the template's chisel-cut build and
 * supply-chain evidence pipeline, not any real application.
 *
 * Build (deferred until the pipeline is wired):
 *   cc -static -Os -o hello hello.c
 */
#include <unistd.h>

int main(void)
{
    static const char msg[] = "hello from a chiseled image\n";
    /* write() lives in libc6_libs; no shell or stdio buffering needed. */
    ssize_t n = write(STDOUT_FILENO, msg, sizeof(msg) - 1);
    return n == (ssize_t)(sizeof(msg) - 1) ? 0 : 1;
}
