from django.views.generic.list import ListView
from django.db.models import Count, Sum
from .forms import ExpenseSearchForm
from .models import Expense, Category
from .reports import summary_per_category


class ExpenseListView(ListView):
    model = Expense
    paginate_by = 5

    def get_queryset(self):
        queryset = Expense.objects.all()
        form = ExpenseSearchForm(self.request.GET)
        if form.is_valid():
            name = form.cleaned_data.get('name', '').strip()
            if name:
                queryset = queryset.filter(name__icontains=name)

            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            if date_from:
                queryset = queryset.filter(date__gte=date_from)
            if date_to:
                queryset = queryset.filter(date__lte=date_to)

            categories = form.cleaned_data.get('categories')
            if categories:
                queryset = queryset.filter(category__in=categories)

        sort = self.request.GET.get('sort', 'date')  
        if sort in ['category', '-category', 'date', '-date']:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context.update({
            'form': ExpenseSearchForm(self.request.GET),
            'object_list': queryset,
            'summary_per_category': summary_per_category(queryset),
            'summary_per_year_month': (
                Expense.objects.extra({'year_month': "strftime('%%Y-%%m', date)"})
                .values('year_month')
                .annotate(total=Sum('amount'))
                .order_by('-year_month')
            ),
            'total_spent': queryset.aggregate(total=Sum('amount'))['total'] or 0,
        })
        return context

class CategoryListView(ListView):
    model = Category
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        context['object_list'] = Category.objects.annotate(expense_count=Count('expense'))
        
        return context
