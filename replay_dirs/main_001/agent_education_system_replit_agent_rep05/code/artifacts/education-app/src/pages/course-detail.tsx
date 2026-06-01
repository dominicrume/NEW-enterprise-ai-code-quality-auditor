import React, { useEffect } from "react";
import { useLocation, useParams, Link } from "wouter";
import { useGetCourse, getGetCourseQueryKey } from "@workspace/api-client-react";
import { Layout } from "@/components/layout";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, BookOpen, Clock, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

export default function CourseDetail() {
  const [, setLocation] = useLocation();
  const params = useParams();
  const courseId = params.id ? parseInt(params.id, 10) : 0;

  useEffect(() => {
    if (!localStorage.getItem("auth_token")) {
      setLocation("/login");
    }
  }, [setLocation]);

  const { data: course, isLoading, error } = useGetCourse(courseId, {
    query: {
      enabled: !!courseId && !!localStorage.getItem("auth_token"),
      queryKey: getGetCourseQueryKey(courseId)
    }
  });

  if (error) {
    return (
      <Layout>
        <div className="py-12 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-destructive/10 text-destructive mb-4">
            <BookOpen className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-foreground mb-2">Course Not Found</h2>
          <p className="text-muted-foreground mb-6">The course you are looking for doesn't exist or you don't have access to it.</p>
          <Button asChild>
            <Link href="/courses">Return to Catalog</Link>
          </Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-6">
        <Button variant="ghost" size="sm" asChild className="mb-6 text-muted-foreground hover:text-foreground -ml-3">
          <Link href="/courses" data-testid="link-back">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to courses
          </Link>
        </Button>

        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-8 w-32 rounded-full" />
            <Skeleton className="h-12 w-3/4" />
            <Skeleton className="h-6 w-full max-w-2xl" />
            <Skeleton className="h-6 w-2/3" />
          </div>
        ) : course && (
          <div className="max-w-4xl">
            <div className="flex items-center gap-3 mb-4">
              <Badge className="px-3 py-1 text-sm font-medium rounded-full" data-testid="badge-category">
                {course.category}
              </Badge>
              <span className="text-sm text-muted-foreground flex items-center gap-1.5" data-testid="text-lesson-count">
                <BookOpen className="w-4 h-4" />
                {course.lessonCount} lessons
              </span>
            </div>
            
            <h1 className="text-4xl font-extrabold tracking-tight text-foreground mb-6" data-testid="text-course-title">
              {course.title}
            </h1>
            
            <div className="prose prose-slate dark:prose-invert max-w-none mb-12 text-lg text-muted-foreground" data-testid="text-course-desc">
              {course.description}
            </div>
            
            <Separator className="my-8" />
            
            <div className="mb-8">
              <h2 className="text-2xl font-bold tracking-tight mb-6">Course Curriculum</h2>
              
              {course.lessons.length > 0 ? (
                <Accordion type="single" collapsible className="w-full space-y-4" data-testid="list-lessons">
                  {course.lessons.map((lesson, index) => (
                    <AccordionItem key={lesson.id} value={`item-${lesson.id}`} className="bg-card border border-border/50 rounded-xl overflow-hidden shadow-sm data-[state=open]:border-primary/30 transition-colors">
                      <AccordionTrigger className="px-6 py-4 hover:no-underline hover:bg-muted/30 group">
                        <div className="flex items-center text-left gap-4">
                          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-semibold text-sm group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                            {index + 1}
                          </div>
                          <span className="text-lg font-medium" data-testid={`text-lesson-title-${lesson.id}`}>
                            {lesson.title}
                          </span>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="px-6 pb-6 pt-2">
                        <div className="pl-12">
                          <div className="prose prose-slate dark:prose-invert max-w-none" data-testid={`text-lesson-content-${lesson.id}`}>
                            {lesson.content}
                          </div>
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              ) : (
                <div className="p-8 text-center bg-muted/30 rounded-xl border border-border border-dashed">
                  <p className="text-muted-foreground">No lessons have been added to this course yet.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
