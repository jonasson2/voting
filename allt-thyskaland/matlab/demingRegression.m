function p = demingRegression(x, y, lambda, constrainTo0)
% x,y - measured data
% constrainTo0 - 1 if the intercept is to be constrained to zero
% lambda - ratio of the variance of y and x
if nargin < 3, lambda = 1; end
if nargin < 4, constrainTo0 = 0; end
if isempty(x)
    slope=nan;
    intercept=nan;
else
    if constrainTo0==1
        intercept=0;
        sxx=sum(x.^2);
        syy=sum(y.^2);
        sxy=sum(x.*y);
        slope=(-lambda*sxx+syy+sqrt(4*lambda*sxy^2+(lambda*sxx-syy)^2))/(2*sxy);
    else
        c_xy=cov(x(:),y(:));
        sxx=c_xy(1,1);
        sxy=c_xy(1,2);
        syy=c_xy(2,2);
        slope=(syy-lambda*sxx+sqrt((syy-lambda*sxx)^2+4*lambda*sxy^2))/(2*sxy);
        intercept=mean(y)-slope*mean(x);
    end
end
p = [slope, intercept];
